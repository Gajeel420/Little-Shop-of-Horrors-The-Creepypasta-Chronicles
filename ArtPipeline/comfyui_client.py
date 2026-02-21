"""
comfyui_client.py
=================
Reusable ComfyUI API client for the Feed Me: Descent into Madness art pipeline.

Handles:
  - Queuing prompts via the /prompt endpoint
  - Tracking job completion via WebSocket
  - Downloading finished images
  - Seed injection so every asset can be reproduced exactly
  - Retry logic with exponential back-off for network blips on vast.ai

Usage:
    from comfyui_client import ComfyUIClient
    client = ComfyUIClient("http://<vast-ip>:8188")
    images = client.generate(workflow_dict, output_node_id="save_image")
"""

from __future__ import annotations

import copy
import json
import random
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import requests
import websocket
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()


class ComfyUIClient:
    """Thin wrapper around the ComfyUI HTTP + WebSocket API."""

    def __init__(self, host: str = "http://127.0.0.1:8188", timeout: int = 600):
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(
        self,
        workflow: dict,
        seed: int | None = None,
        seed_node_ids: list[str] | None = None,
        output_node_ids: list[str] | None = None,
    ) -> list[bytes]:
        """
        Queue a workflow, wait for completion, return list of PNG bytes.

        Args:
            workflow:         ComfyUI workflow dict (loaded from a .json file).
            seed:             Fixed seed. If None, a random seed is used.
            seed_node_ids:    Node IDs whose 'seed' input should be set.
                              If None, all KSampler nodes are auto-detected.
            output_node_ids:  Node IDs to pull output images from.
                              If None, all SaveImage / PreviewImage nodes used.
        """
        wf = copy.deepcopy(workflow)
        resolved_seed = seed if seed is not None else random.randint(0, 2**32 - 1)

        self._inject_seeds(wf, resolved_seed, seed_node_ids)

        prompt_id = self._queue_prompt(wf)
        console.log(f"  [dim]Queued prompt_id={prompt_id}  seed={resolved_seed}[/dim]")

        self._wait_for_completion(prompt_id)

        images = self._fetch_images(prompt_id, output_node_ids)
        console.log(f"  [green]✓[/green] {len(images)} image(s) received")
        return images

    def queue_batch(
        self,
        jobs: list[dict],
        output_dir: Path,
        filename_fn=None,
    ) -> list[Path]:
        """
        Run a list of job dicts sequentially, save to output_dir.

        Each job dict: {"workflow": {...}, "seed": int, "filename": "foo.png", ...}
        Returns list of saved file paths.
        """
        saved: list[Path] = []
        output_dir.mkdir(parents=True, exist_ok=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Generating assets...", total=len(jobs))

            for i, job in enumerate(jobs):
                name = job.get("filename", f"asset_{i:04d}.png")
                progress.update(task, description=f"[{i+1}/{len(jobs)}] {name}")

                images = self.generate(
                    job["workflow"],
                    seed=job.get("seed"),
                    seed_node_ids=job.get("seed_node_ids"),
                    output_node_ids=job.get("output_node_ids"),
                )

                # If multiple images returned, use first (or save all with suffix)
                for img_idx, img_bytes in enumerate(images):
                    suffix = f"_{img_idx}" if len(images) > 1 and img_idx > 0 else ""
                    stem = Path(name).stem
                    ext = Path(name).suffix or ".png"
                    out_path = output_dir / f"{stem}{suffix}{ext}"
                    out_path.write_bytes(img_bytes)
                    saved.append(out_path)

                progress.advance(task)

        return saved

    # ── Internal ───────────────────────────────────────────────────────────────

    def _queue_prompt(self, workflow: dict) -> str:
        payload = json.dumps({"prompt": workflow, "client_id": self.client_id}).encode()
        resp = self._post("/prompt", payload)
        return resp["prompt_id"]

    def _wait_for_completion(self, prompt_id: str) -> None:
        ws_url = f"ws://{self.host.split('://')[-1]}/ws?clientId={self.client_id}"
        ws = websocket.WebSocket()

        retries = 4
        for attempt in range(retries):
            try:
                ws.connect(ws_url, timeout=self.timeout)
                break
            except Exception as exc:
                if attempt == retries - 1:
                    raise RuntimeError(f"WebSocket connect failed after {retries} tries: {exc}") from exc
                time.sleep(2 ** attempt)

        try:
            deadline = time.time() + self.timeout
            while time.time() < deadline:
                raw = ws.recv()
                if not raw:
                    continue
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                mtype = msg.get("type")
                data  = msg.get("data", {})

                if mtype == "executing" and data.get("node") is None:
                    if data.get("prompt_id") == prompt_id:
                        return  # done

                if mtype == "execution_error":
                    if data.get("prompt_id") == prompt_id:
                        raise RuntimeError(f"ComfyUI execution error: {data}")
        finally:
            ws.close()

        raise TimeoutError(f"Generation did not complete within {self.timeout}s")

    def _fetch_images(self, prompt_id: str, output_node_ids: list[str] | None) -> list[bytes]:
        history = self._get(f"/history/{prompt_id}")
        if prompt_id not in history:
            raise RuntimeError(f"prompt_id {prompt_id} not found in history")

        outputs = history[prompt_id]["outputs"]
        images: list[bytes] = []

        for node_id, node_output in outputs.items():
            if output_node_ids and node_id not in output_node_ids:
                continue
            for img_info in node_output.get("images", []):
                params = urllib.parse.urlencode({
                    "filename": img_info["filename"],
                    "subfolder": img_info.get("subfolder", ""),
                    "type": img_info.get("type", "output"),
                })
                url = f"{self.host}/view?{params}"
                images.append(self._http_get_bytes(url))

        return images

    # ── Seed injection ─────────────────────────────────────────────────────────

    def _inject_seeds(
        self,
        workflow: dict,
        seed: int,
        node_ids: list[str] | None,
    ) -> None:
        """Set seed on KSampler / KSamplerAdvanced nodes."""
        for node_id, node in workflow.items():
            is_target = (
                node_ids is None
                or node_id in node_ids
            )
            class_type = node.get("class_type", "")
            if is_target and "KSampler" in class_type:
                if "inputs" in node and "seed" in node["inputs"]:
                    node["inputs"]["seed"] = seed

    # ── HTTP helpers ───────────────────────────────────────────────────────────

    def _post(self, path: str, data: bytes) -> Any:
        for attempt in range(4):
            try:
                resp = requests.post(
                    f"{self.host}{path}",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as exc:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)

    def _get(self, path: str) -> Any:
        for attempt in range(4):
            try:
                resp = requests.get(f"{self.host}{path}", timeout=30)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as exc:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)

    def _http_get_bytes(self, url: str) -> bytes:
        for attempt in range(4):
            try:
                resp = requests.get(url, timeout=60)
                resp.raise_for_status()
                return resp.content
            except requests.RequestException as exc:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
