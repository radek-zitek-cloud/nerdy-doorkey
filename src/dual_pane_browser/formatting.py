"""Formatting helpers for file metadata."""

from __future__ import annotations

from datetime import datetime


def format_size(size: int) -> str:
    """Convert a byte size to a short human-readable string."""
    units = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]
    value = float(size)
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    unit = units[index]
    if unit == "B":
        return f"{int(value)}{unit}"
    formatted = f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{formatted}{unit}"


def format_timestamp(timestamp: datetime) -> str:
    """Render a timestamp using the requested short format."""
    return timestamp.strftime("%b %d %H:%M")


__all__ = ["format_size", "format_timestamp"]
