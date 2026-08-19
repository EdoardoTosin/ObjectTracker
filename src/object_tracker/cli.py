"""Command-line interface for ObjectTracker.

Usage examples
--------------
    object-tracker
    object-tracker --objects "person,car,traffic light"
    object-tracker --objects all --no-window
    object-tracker --dual-rate --camera-index 1
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from object_tracker import __version__

app = typer.Typer(
    name="object-tracker",
    help="Real-time object detection and event-based video recording for USB cameras.",
    add_completion=False,
    rich_markup_mode="rich",
    invoke_without_command=True,
)

_console = Console()
_err = Console(stderr=True, style="bold red")


def _version_callback(value: bool) -> None:
    if value:
        _console.print(f"ObjectTracker {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Print version and exit.",
        ),
    ] = None,
    camera_index: Annotated[
        int, typer.Option("--camera-index", help="Index of the camera device to use.")
    ] = 0,
    objects: Annotated[
        str | None,
        typer.Option(
            "--objects",
            help='Comma-separated object names to detect (e.g. "person,car,traffic light"), '
            "or 'all'. Defaults to the value in config.yaml.",
        ),
    ] = None,
    window: Annotated[
        bool,
        typer.Option("--window/--no-window", help="Show the live video feed window."),
    ] = True,
    dual_rate: Annotated[
        bool,
        typer.Option(
            "--dual-rate/--fixed-rate",
            help="Adapt to cameras that switch between a normal (~30 fps) and a "
            "night (~4-5 fps) mode, restarting recordings cleanly on rate changes.",
        ),
    ] = False,
    log_level: Annotated[
        str,
        typer.Option("--log-level", help="Logging verbosity.", case_sensitive=False),
    ] = "INFO",
    config_file: Annotated[
        Path | None, typer.Option("--config", help="Path to a config.yaml file.")
    ] = None,
    models_dir: Annotated[
        Path | None,
        typer.Option(
            "--models-dir",
            help="Directory containing the .names/.pbtxt/.pb model files.",
        ),
    ] = None,
    recordings_dir: Annotated[
        Path | None,
        typer.Option(
            "--recordings-dir", help="Directory recordings are written under."
        ),
    ] = None,
) -> None:
    """Start live detection and event-based recording."""
    from object_tracker.core.app_logger import configure_logging
    from object_tracker.core.config import DEFAULT_CONFIG_FILE, resolve_config
    from object_tracker.core.tracker import run_tracker

    configure_logging(log_level)

    try:
        cfg = resolve_config(
            config_path=config_file or DEFAULT_CONFIG_FILE,
            camera_index=camera_index,
            objects=objects,
            show_window=window,
            dual_rate=dual_rate,
            log_level=log_level,
            models_dir=models_dir,
            recordings_dir=recordings_dir,
        )
    except Exception as exc:
        _err.print(f"Configuration error: {exc}")
        raise typer.Exit(1)

    _console.rule("[bold]ObjectTracker")
    _console.print(
        f"Camera index [cyan]{cfg.camera_index}[/cyan] | "
        f"mode: [cyan]{'dual-rate' if cfg.dual_rate else 'fixed-rate'}[/cyan] | "
        "press Ctrl+C to stop.\n"
    )

    try:
        exit_code = run_tracker(cfg)
    except Exception as exc:
        _err.print(str(exc))
        raise typer.Exit(1)

    if exit_code == 0:
        _console.print("\n[green]Stopped.[/green]")
    else:
        _console.print("\n[red]Stopped with errors.[/red]")
    raise typer.Exit(exit_code)
