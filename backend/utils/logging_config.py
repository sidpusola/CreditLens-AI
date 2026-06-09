from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
