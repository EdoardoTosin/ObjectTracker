# Contributing to ObjectTracker Project

Thank you for your interest in contributing to this project! We welcome all contributions, including bug fixes, feature requests, documentation improvements, and code enhancements.

## Getting Started

1. **Fork the Repository**  
   Create a personal fork of the repository by clicking the "Fork" button on GitHub.

2. **Clone Your Fork**  
   Clone your forked repository to your local machine:
   ```bash
   git clone https://github.com/EdoardoTosin/ObjectTracker
   cd ObjectTracker
   ```

3. **Create a Branch**  
   Create a feature branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Install Dependencies**  
   Ensure you have Python 3.10+ and [uv](https://docs.astral.sh/uv/) installed, then install the project including dev dependencies:
   ```bash
   uv sync --all-groups
   ```

5. **Run the Checks**  
   Ensure your changes pass linting, formatting, type-checking, and the test suite before opening a pull request:
   ```bash
   uv run ruff check src/ tests/
   uv run black --check src/ tests/
   uv run mypy src/
   uv run pytest
   ```

## Making Changes

See [docs/development.md](docs/development.md) for the architecture and testing approach before making non-trivial changes.

- Follow the existing code style; `ruff` and `black` enforce most of it automatically.
- Keep engines/modules stateless where possible and prefer small, pure, testable functions over large stateful ones.
- Add or update tests for any behavioral change: `pytest` runs with coverage enabled and fails below the threshold set in `pyproject.toml`.
- Add appropriate documentation for new features (README and/or `docs/`).

## Submitting a Pull Request

1. **Push Your Branch**  
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**  
   Go to the GitHub page of your forked repository and click on "New Pull Request."

3. **Description**  
   Provide a clear description of the changes you made, why they are necessary, and any related issues.

## Code Style Guidelines

- Follow **PEP 8** for Python code.  
- Use descriptive variable and function names.  
- Keep functions small and focused on a single task.

## Reporting Issues

If you encounter any issues or have feature suggestions, please open an issue on GitHub. Be sure to provide as much detail as possible, including steps to reproduce the issue.

## Licensing

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing!
