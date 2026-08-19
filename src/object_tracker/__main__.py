"""Entry point for the ObjectTracker CLI."""

from __future__ import annotations


def main() -> None:
    from object_tracker.cli import app

    app()


if __name__ == "__main__":
    main()
