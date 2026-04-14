"""
Dialogue / typewriter system.
DialogueBox handles queued text lines with a typewriter effect.
"""

import pygame
import random
import string
from constants import *


class DialogueBox:
    """
    Renders a text box at the bottom of the screen.
    Call push(lines) to queue dialogue.
    Call advance() or check ready() to step through.
    """

    CHARS_PER_SEC = 35   # typewriter speed

    def __init__(self, font, box_rect: pygame.Rect):
        self.font     = font
        self.rect     = box_rect
        self._queue   = []        # list of str
        self._current = ""        # full target string
        self._shown   = 0.0       # chars revealed so far
        self._done    = False
        self._glitch  = False     # creepypasta glitch mode

    # ── Public API ────────────────────────────────────────────────────────────

    def push(self, lines, glitch=False):
        """Queue one or more dialogue lines (str or list[str])."""
        if isinstance(lines, str):
            lines = [lines]
        self._queue.extend(lines)
        self._glitch = glitch
        if not self._current:
            self._next()

    def advance(self):
        """Skip to end of current line, or advance to next."""
        if not self._done:
            self._shown = float(len(self._current))
            self._done  = True
        elif self._queue:
            self._next()

    def ready(self):
        """True when all queued lines have been shown."""
        return self._done and not self._queue

    def is_empty(self):
        return not self._current and not self._queue

    def clear(self):
        self._queue   = []
        self._current = ""
        self._shown   = 0.0
        self._done    = True

    def update(self, dt):
        if self._current and not self._done:
            self._shown = min(len(self._current),
                              self._shown + self.CHARS_PER_SEC * dt)
            if self._shown >= len(self._current):
                self._done = True

    def draw(self, surf: pygame.Surface):
        # Background box
        pygame.draw.rect(surf, BLACK, self.rect)
        pygame.draw.rect(surf, WHITE, self.rect, 2)

        if not self._current:
            return

        n = int(self._shown)
        text = self._current[:n]
        if self._glitch and not self._done:
            text = _glitch_tail(text, tail_len=3)

        # Word-wrap inside box
        inner = self.rect.inflate(-12, -10)
        _render_wrapped(surf, self.font, text, WHITE, inner)

        # Blinking arrow when done and more lines
        if self._done and (self._queue or not self.ready()):
            if pygame.time.get_ticks() % 1000 < 600:
                arrow = self.font.render("▼", True, WHITE)
                surf.blit(arrow, (self.rect.right - 16, self.rect.bottom - 16))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _next(self):
        if self._queue:
            self._current = self._queue.pop(0)
            self._shown   = 0.0
            self._done    = False
        else:
            self._current = ""
            self._done    = True


def _glitch_tail(text, tail_len=3):
    """Replace the last few visible chars with noise."""
    if len(text) <= tail_len:
        return text
    noise = "".join(random.choice(string.ascii_letters + "█▓▒░") for _ in range(tail_len))
    return text[:-tail_len] + noise


def _render_wrapped(surf, font, text, color, rect):
    """Simple word-wrap renderer."""
    words  = text.split(" ")
    line   = ""
    y      = rect.top
    lh     = font.get_linesize()
    for word in words:
        test = line + (" " if line else "") + word
        if font.size(test)[0] <= rect.width:
            line = test
        else:
            if line:
                surf.blit(font.render(line, True, color), (rect.left, y))
                y += lh
            line = word
        if y + lh > rect.bottom:
            break
    if line and y + lh <= rect.bottom:
        surf.blit(font.render(line, True, color), (rect.left, y))


# ── Speaker portrait stub ─────────────────────────────────────────────────────

def draw_portrait(surf, font, name, color, rect: pygame.Rect):
    """Draw a simple text-based portrait box."""
    pygame.draw.rect(surf, BLACK, rect)
    pygame.draw.rect(surf, color, rect, 2)
    initials = name[:2].upper()
    label = font.render(initials, True, color)
    surf.blit(label, label.get_rect(center=rect.center))
