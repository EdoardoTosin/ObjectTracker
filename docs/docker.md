# Docker

## Build and Run with Compose

```bash
docker compose up --build
```

This builds the image with uv, maps `/dev/video0` into the container, mounts `./recordings` and `./config.yaml`, and runs headless (`--no-window`) by default.

## Build and Run without Compose

```bash
docker build -t object-tracker .
docker run --rm \
  --device /dev/video0:/dev/video0 \
  -v $(pwd)/recordings:/app/recordings \
  object-tracker
```

## What the Image Does

- Base image: `python:3.11-slim`, with the runtime libraries OpenCV's video I/O needs (`libgl1`, `libglib2.0-0`).
- Installs [uv](https://docs.astral.sh/uv/) and syncs dependencies (`--no-dev`) in a layer separate from the source copy, so a source-only change doesn't re-download dependencies.
- Entry point is `uv run object-tracker`; the default command passes `--no-window --objects all` (a container has no display, see [Notes](#notes) below).

## Customizing

| What | Where |
|---|---|
| Camera device | `docker-compose.yml`'s `devices:` entry, e.g. `/dev/video1:/dev/video1` for a second camera |
| Objects to detect | `docker-compose.yml`'s `command:`, or bake a different `config.yaml` into the mounted volume |
| Recording location | `docker-compose.yml`'s `./recordings:/app/recordings` volume mount |
| Config file | `docker-compose.yml`'s `./config.yaml:/app/config.yaml:ro` volume mount (read-only) |

## Notes

> [!NOTE]
> Containers have no display, so the default command always passes `--no-window`. Recordings and logs are still produced normally.

> [!IMPORTANT]
> The container needs the camera device passed through explicitly via `--device` (or `devices:` in Compose); Docker does not expose USB devices to a container by default. See [Troubleshooting: Docker](troubleshooting.md#docker) if the container can't see the camera.
