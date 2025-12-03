# GAIA Development Guide

**Table of Contents**
- [Introduction](#introduction)
- [Before you start](#before-you-start)
  - [System Requirements](#system-requirements)
  - [Software Requirements](#software-requirements)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
- [Support](#support)
- [License](#license)

# Introduction

GAIA is an open-source framework that runs generative AI applications on AMD hardware. GAIA uses the [ONNX Runtime GenAI (aka OGA)](https://github.com/microsoft/onnxruntime-genai/tree/main?tab=readme-ov-file) backend via [Lemonade Server](https://lemonade-server.ai/) tool for running Large Language Models (LLMs).

GAIA utilizes both NPU and iGPU on Ryzen AI systems for optimal performance on 300 series processors or above.

# Before you start

## System Requirements

- OS: Windows 11 Pro, 24H2 or Ubuntu 22.04 LTS / 24.04 LTS (64-bit)
- RAM: Minimum 16GB
- CPU: Ryzen AI 300-series processor (e.g., Ryzen AI 9 HX 370)
- NPU Driver Versions: `32.0.203.240` and newer
- Storage: 20GB free space
- Tested Configuration: ASUS ProArt (HN7306W) Laptop

## Software Requirements

- **Python 3.12+**: Download from [python.org](https://www.python.org/downloads/)
- **Git**: For version control
- **Lemonade Server**: LLM backend server for GAIA - download from [lemonade-server.ai](https://lemonade-server.ai/)
- **uv** (recommended): Fast Python package manager - install from [docs.astral.sh/uv](https://docs.astral.sh/uv/)

# Prerequisites

## Windows Prerequisites

1. **Install Python 3.12**:
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, **check "Add Python to PATH"**
   - Verify installation: `python --version`

2. **Install Lemonade Server**:
   - Go to https://lemonade-server.ai/ and download the Windows installer
   - Follow the installation instructions provided on the website
   - Lemonade Server will be used as the backend for running LLMs with GAIA

## Linux/Ubuntu Prerequisites

1. **Install Python 3.12**:
   ```bash
   # Ubuntu 24.04 (has Python 3.12 by default)
   sudo apt update
   sudo apt install python3.12 python3.12-venv python3-pip

   # Ubuntu 22.04 (use deadsnakes PPA)
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.12 python3.12-venv
   ```

2. **Verify installation**:
   ```bash
   python3.12 --version
   ```

3. **Install Lemonade Server**:
   - Go to https://lemonade-server.ai/ and download the Linux version
   - Follow the Linux installation instructions provided on the website
   - Lemonade Server will be used as the backend for running LLMs with GAIA

### WSL (Windows Subsystem for Linux) Note
If you're using WSL, install Python inside WSL rather than trying to use the Windows installation. This ensures better compatibility and performance.

# Setup and Installation

## Option A: Using uv (Recommended - 10-100x Faster)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that handles virtual environments and package installation much faster than pip.

1. **Install uv**:

   **Windows (PowerShell)**:
   ```powershell
   irm https://astral.sh/uv/install.ps1 | iex
   ```

   **Linux/macOS**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone GAIA repo**:
   ```bash
   git clone https://github.com/amd/gaia.git
   cd gaia
   ```

3. **Create virtual environment and install dependencies**:
   ```bash
   # Create venv with Python 3.12 (uv will download Python if needed)
   uv venv .venv --python 3.12

   # Activate the environment
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate

   # Install GAIA with dev dependencies
   uv pip install -e .[dev]

   # Or with all extras
   uv pip install -e .[dev,eval,talk,rag]
   ```

## Option B: Using Standard Python venv + pip

1. **Clone GAIA repo**:
   ```bash
   git clone https://github.com/amd/gaia.git
   cd gaia
   ```

2. **Create and activate a virtual environment**:

   **Windows (PowerShell)**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **Windows (Command Prompt)**:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate.bat
   ```

   **Linux/Ubuntu/WSL/macOS**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   You should see `(.venv)` prefix in your terminal prompt when activated.

3. **Upgrade pip**:
   ```bash
   python -m pip install --upgrade pip
   ```

4. **Install GAIA dependencies**:
   ```bash
   # Linux/Windows
   pip install -e .[dev]

   # macOS (zsh shell requires quotes)
   pip install -e ".[dev]"
   ```

   ⚠️ NOTE: If actively developing, use `-e` switch to enable editable mode and create links to sources instead.

   ⚠️ NOTE: **macOS users**: If you get an error like `zsh: no matches found`, you need to quote the package specification: `pip install -e ".[dev]"`

   ⚠️ NOTE: Check `./setup.py` for additional packages that support extra features in the CLI tool:
   - Linux/Windows: `pip install -e .[dev,eval,talk,rag]`
   - macOS: `pip install -e ".[dev,eval,talk,rag]"`

5. For detailed information about using the Chat SDK and CLI chat features, see the [Chat SDK Documentation](./chat.md).

## Deactivating the Virtual Environment

When you're done working, deactivate the virtual environment:
```bash
deactivate
```

## Dependency Management

For information on managing dependencies and configuring Dependabot for automated updates, see the [Dependency Management Guide](./dependency-management.md).

# Running GAIA

Once the installation and environment variables are set, run the following:

1. Start the Lemonade server (required for LLM operations):
    ```bash
    lemonade-server serve
    ```
    Keep this running in a separate terminal window.

1. Run `gaia -v` in the terminal to verify the installation. You should see a similar output:
    ```bash
    0.13.1
    ```
1. Run `gaia -h` to see CLI options.
1. Try the chat feature with a simple query:
    ```bash
    gaia chat "What is artificial intelligence?"
    ```
    Or start an interactive chat session:
    ```bash
    gaia chat
    ```

## Running Electron Applications

GAIA includes Electron-based GUI applications. To run the JAX (Jira Agent Experience) app locally:

```bash
# Linux/Mac
./src/gaia/apps/jira/webui/run.sh

# Windows
.\src\gaia\apps\jira\webui\run.ps1
```

This will build the installer and launch the JAX application in development mode. The installer will be created in `src/gaia/apps/jira/webui/out/make/`.

# Troubleshooting

## Common Issues

### "python" command not found (Windows)

- Ensure Python was installed with "Add to PATH" checked
- Or use `py -3.12` instead of `python`
- Try reinstalling Python and checking the PATH option

### "python3.12" command not found (Linux)

```bash
# Add deadsnakes PPA for newer Python versions
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv
```

### Virtual Environment Activation Issues

**Windows PowerShell execution policy**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Use full path if needed**:
```powershell
.\.venv\Scripts\Activate.ps1
```

### pip Installation Errors

If you encounter pip installation errors:
1. Ensure you're using Python 3.12 or later
2. Try running: `pip install --upgrade pip`
3. Try deleting pip cache typically under: _C:\Users\<username>\AppData\Local\pip\cache_
4. Make sure there are no spaces in your project or pip file cache paths

### Model Loading Issues

1. Check available system memory
2. Verify model compatibility with your hardware
3. Ensure all dependencies are correctly installed

### Environment Variable Issues

If GAIA is not working correctly:

1. Verify the installation completed successfully by checking the log files
2. Ensure all dependencies are installed correctly
3. Check that you're in the correct virtual environment:
   ```bash
   # Linux/Ubuntu/WSL/macOS
   source .venv/bin/activate

   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```
4. Verify the virtual environment is activated (you should see `(.venv)` in your terminal prompt)
5. Try restarting your terminal or command prompt

# Support

Report any issues to the GAIA team at `gaia@amd.com` or create an [issue](https://github.com/amd/gaia/issues) on the [GAIA GitHub repo](https://github.com/amd/gaia.git).

# License

[MIT License](../LICENSE.md)

Copyright(C) 2024-2025 Advanced Micro Devices, Inc. All rights reserved.
SPDX-License-Identifier: MIT
