"""Environment setup that must happen before pygame is imported."""

import os
import sys


def configure_pygame_environment(platform: str) -> None:
    """Apply platform defaults without overriding explicit user settings."""
    if platform == "darwin":
        os.environ.setdefault("SDL_VIDEODRIVER", "cocoa")
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


configure_pygame_environment(sys.platform)
