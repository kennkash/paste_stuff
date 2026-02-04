# Setting Up the Development Environment

This project uses [uv](https://github.com/astral-sh/uv) for Python dependency management and virtual environments.

## Prerequisites

Install uv if you haven’t already:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: Install via pip
pip install uv
```

## Setup Instructions

After cloning this repository, set up the environment:

```bash
# Navigate to the project directory
cd your-project-name

# Create virtual environment and install dependencies
uv sync
```

That’s it! The `uv sync` command will:

- Create a virtual environment (if it doesn’t exist)
- Install all dependencies from the lockfile
- Ensure your environment matches the exact versions specified

## Activating the Virtual Environment

```bash
# On macOS and Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

## Adding New Dependencies

If you need to add new packages:

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

## Updating Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update a specific package
uv add package-name --upgrade
```

## Running Python Scripts

You can run Python scripts without activating the environment:

```bash
uv run python your_script.py
```

Or activate the environment first and run normally:

```bash
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python your_script.py
```