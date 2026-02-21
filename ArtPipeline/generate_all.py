"""
generate_all.py
===============
Master runner that calls all three generators in sequence.
Designed to run overnight on a vast.ai instance.

Run:
    python generate_all.py --host http://<vast-ip>:8188
    python generate_all.py --host http://<vast-ip>:8188 --stage 1
    python generate_all.py --host http://<vast-ip>:8188 --only backgrounds
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()

ROOT = Path(__file__).parent


def run(cmd: list[str]) -> int:
    console.rule(f"[bold cyan]{' '.join(cmd[1:])}[/bold cyan]")
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run full art pipeline")
    parser.add_argument("--host",  default="http://127.0.0.1:8188")
    parser.add_argument("--stage", default="all",
                        help="Limit backgrounds to stage: all | 1 | 2 | 3 | special")
    parser.add_argument("--only",  default=None,
                        choices=["backgrounds", "sprites", "misc"],
                        help="Run only one generator")
    parser.add_argument("--seed",  type=int, default=42)
    args = parser.parse_args()

    py = sys.executable
    errors = 0

    if args.only in (None, "backgrounds"):
        rc = run([py, "generate_backgrounds.py",
                  "--host", args.host,
                  "--stage", args.stage,
                  "--seed", str(args.seed)])
        errors += rc

    if args.only in (None, "sprites"):
        rc = run([py, "generate_sprites.py",
                  "--host", args.host,
                  "--seed", str(args.seed + 10000)])
        errors += rc

    if args.only in (None, "misc"):
        rc = run([py, "generate_misc.py",
                  "--host", args.host,
                  "--seed", str(args.seed + 20000)])
        errors += rc

    console.rule("[bold green]Pipeline complete[/bold green]" if errors == 0
                 else "[bold red]Pipeline finished with errors[/bold red]")

    if errors:
        console.print(f"[red]{errors} generator(s) reported errors.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
