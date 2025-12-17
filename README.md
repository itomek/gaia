# <img src="src/gaia/img/gaia.ico" alt="GAIA Logo" width="64" height="64" style="vertical-align: middle;"> GAIA: AI Agent Framework for AMD Ryzen AI

[![GAIA Build Installer](https://github.com/amd/gaia/actions/workflows/build_installer.yml/badge.svg)](https://github.com/amd/gaia/tree/main/tests "Check out our build")
[![GAIA Installer Test](https://github.com/amd/gaia/actions/workflows/test_installer.yml/badge.svg)](https://github.com/amd/gaia/tree/main/tests "Check out our installer tests")
[![GAIA CLI Tests](https://github.com/amd/gaia/actions/workflows/test_gaia_cli.yml/badge.svg)](https://github.com/amd/gaia/tree/main/tests "Check out our cli tests")
[![Latest Release](https://img.shields.io/github/v/release/amd/gaia?include_prereleases)](https://github.com/amd/gaia/releases/latest "Download the latest release")
[![PyPI](https://img.shields.io/pypi/v/amd-gaia)](https://pypi.org/project/amd-gaia/)
[![OS - Windows](https://img.shields.io/badge/OS-Windows-blue)](https://github.com/amd/gaia/blob/main/docs/installer.md "Windows installer")
[![OS - Linux](https://img.shields.io/badge/OS-Linux-green)](https://github.com/amd/gaia/blob/main/README.md#linux-installation "Linux support")
[![OS - macOS](https://img.shields.io/badge/OS-macOS-black)](https://github.com/amd/gaia/blob/main/docs/dev.md "macOS support")
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub issues](https://img.shields.io/github/issues/amd/gaia)](https://github.com/amd/gaia/issues)
[![GitHub downloads](https://img.shields.io/github/downloads/amd/gaia/total.svg)](https://github.com/amd/gaia/releases)
[![Discord](https://img.shields.io/badge/Discord-Join%20Community-7289DA?logo=discord&logoColor=white)](https://discord.com/channels/1392562559122407535/1402013282495102997)

<img src="https://img.youtube.com/vi/_PORHv_-atI/maxresdefault.jpg" style="display: block; margin: auto;" />

**GAIA** is AMD's open-source framework for building intelligent AI agents that run **100% locally** on AMD Ryzen AI hardware. Keep your data private, eliminate cloud costs, and deploy in air-gapped environments—all with hardware-accelerated performance using AMD NPU.

## What is GAIA?

GAIA is a **framework/SDK** for AI PC agent development, providing:

### **Agent Development Framework**
Build custom AI agents quickly and easily with:
- **Agent Base Class** - Smart orchestration of LLM + your tools
- **Tool System** - Register Python functions as agent capabilities
- **RAG Integration** - Document Q&A with vector search
- **Vision Models** - Extract text from images and documents
- **Voice Integration** - Speech-to-text and text-to-speech
- **Database Mixins** - SQLAlchemy integration for stateful agents
- **Testing Utilities** - Mock LLMs, temporary databases, fixtures

```python
# Build your own agent in minutes
from gaia.agents.base.agent import Agent
from gaia.agents.base.tools import tool

class MyAgent(Agent):
    @tool
    def search_data(query: str) -> dict:
        """Search for data."""
        return {"results": ["item1", "item2"]}

agent = MyAgent()
result = agent.process_query("Find user data")
```

### **Application Packaging System**
Package your agents professionally:
- **Web UI Generation** - Modern React-based interfaces for your agents
- **Windows Installer** - NSIS-based installers with RAUX integration
- **Plugin Discovery** - Agents auto-discovered via `pip install`
- **CLI Integration** - Custom commands under `gaia <your-command>`

**Example agents are maintained in separate repositories** - GAIA is the framework they're built on.

## Why GAIA?

**Framework Features:**

- **100% Local Execution**: All data stays on your machine—perfect for sensitive workloads, compliance requirements, and air-gapped deployments
- **Zero Cloud Costs**: No API fees, no usage limits, no monthly subscriptions—unlimited AI processing at no extra cost
- **Privacy-First**: HIPAA-compliant, GDPR-friendly, no data leaves your network—ideal for healthcare, finance, and enterprise
- **Agent Framework**: Build autonomous agents with tools, state management, and error recovery
- **Ryzen AI Optimized**: Utilizes both NPU and iGPU for accelerated local inference—leverages built-in neural processing and integrated graphics
- **Plugin System**: Distribute agents via PyPI—`pip install` makes them discoverable
- **Database Integration**: SQLAlchemy mixins for stateful agents (coming soon)
- **Vision-Language Models**: Extract text from images with Qwen2.5-VL
- **RAG System**: Document indexing and semantic search for Q&A
- **Voice Integration**: Whisper ASR + Kokoro TTS for speech interaction
- **Web UI Packaging**: Generate modern interfaces for your agents
- **Air-Gapped Ready**: Deploy in secure, isolated networks with no internet dependency

**Platform Support:**
- **Windows 11**: Full GUI and CLI with installer
- **Linux (Ubuntu/Debian)**: Full GUI and CLI via source
- **macOS**: CLI via source (see [Dev Guide](docs/dev.md))

For more details, see our [GAIA Blog Article](https://www.amd.com/en/developer/resources/technical-articles/gaia-an-open-source-project-from-amd-for-running-local-llms-on-ryzen-ai.html) or [Frequently Asked Questions](docs/faq.md).
For Ryzen AI LLM app development similar to GAIA, see [this developer guide](https://ryzenai.docs.amd.com/en/latest/llm/overview.html).

⚠️ **IMPORTANT**: GAIA is specifically designed for **AMD Ryzen AI systems** and uses Lemonade Server for optimal hardware utilization. For more details, see [here](https://www.amd.com/en/products/software/ryzen-ai-software.html#tabs-2733982b05-item-7720bb7a69-tab).

---

## Using GAIA as an SDK

### Install from PyPI

**Using uv (recommended - 10-100x faster):**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
irm https://astral.sh/uv/install.ps1 | iex       # Windows

# Install GAIA
uv pip install amd-gaia
```

**Using pip (traditional):**

```bash
pip install amd-gaia
```

### Build Your First Agent

```python
from gaia.agents.base.agent import Agent
from gaia.agents.base.tools import tool

class WeatherAgent(Agent):
    """Get weather information."""

    def _get_system_prompt(self) -> str:
        return "You are a weather assistant. Use the get_weather tool."

    def _create_console(self):
        from gaia.agents.base.console import AgentConsole
        return AgentConsole()

    def _register_tools(self):
        @tool
        def get_weather(city: str) -> dict:
            """Get current weather for a city."""
            # Your implementation (call weather API)
            return {"city": city, "temperature": 72, "conditions": "Sunny"}

# Use it
agent = WeatherAgent()
result = agent.process_query("What's the weather in Austin?")
print(result)
```

### SDK Features

| Component | Purpose | Documentation |
|-----------|---------|---------------|
| **Agent Base** | Core agent loop & tool execution | [docs/sdk/core](./docs/sdk/core/agent-system.mdx) |
| **ChatSDK** | Chat with memory & streaming | [docs/sdk/sdks/chat](./docs/sdk/sdks/chat.mdx) |
| **RAGSDK** | Document Q&A with vector search | [docs/sdk/sdks/rag](./docs/sdk/sdks/rag.mdx) |
| **VLMClient** | Extract text from images | [docs/sdk/sdks/vlm](./docs/sdk/sdks/vlm.mdx) |
| **AudioClient** | Voice interaction (ASR + TTS) | [docs/sdk/sdks/audio](./docs/sdk/sdks/audio.mdx) |
| **Tool Mixins** | Reusable tool sets | [docs/sdk/mixins](./docs/sdk/mixins/tool-mixins.mdx) |

**[Complete SDK Reference](./docs/sdk/index.mdx)** - Full API documentation with examples

### Build Real-World Agents

**Example: Document Q&A Agent**

```python
from gaia.agents.base.agent import Agent
from gaia.agents.base.tools import tool
from gaia.rag.sdk import RAGSDK, RAGConfig

class DocumentAgent(Agent):
    def __init__(self, docs_path="./docs", **kwargs):
        super().__init__(**kwargs)
        self.rag = RAGSDK(RAGConfig())
        # Index documents
        from pathlib import Path
        for pdf in Path(docs_path).glob("*.pdf"):
            self.rag.index_document(str(pdf))

    def _get_system_prompt(self) -> str:
        return "Answer questions using the search_docs tool."

    def _create_console(self):
        from gaia.agents.base.console import AgentConsole
        return AgentConsole()

    def _register_tools(self):
        @tool
        def search_docs(question: str) -> dict:
            """Search documents for answers."""
            response = self.rag.query(question)
            return {
                "answer": response.text,
                "sources": response.source_files
            }
```

**Package as PyPI Plugin**

```toml
# pyproject.toml
[project]
name = "my-doc-agent"
dependencies = ["amd-gaia>=0.14.0"]

[project.entry-points."gaia.agents"]
doc-agent = "my_agent.agent:DocumentAgent"
```

```bash
pip install my-doc-agent
# Agent auto-discovered!
gaia agents list  # Shows: doc-agent
```

### Developer Resources

- **[SDK Reference](./docs/sdk/index.mdx)** - Complete API documentation with examples
- **[Developer Guide](./docs/dev.md)** - Development environment setup
- **[Testing Guide](./docs/sdk/testing.mdx)** - Testing your agents
- **[Examples](./docs/sdk/examples.mdx)** - Sample agent implementations
- **[Best Practices](./docs/sdk/best-practices.mdx)** - Agent development guidelines

---

## Using GAIA as an Application

GAIA includes pre-built AI tools and a modern web interface.

### Optional Web Interface: GAIA UI (RAUX)

GAIA UI is an optional, modern web-based interface for GAIA, built on the RAUX ([Open-WebUI](https://openwebui.com/) fork) platform. It offers a feature-rich, extensible, and user-friendly experience for interacting with GAIA's AI capabilities. GAIA UI is currently in beta and is being actively integrated with new features and improvements.

> **Note:** GAIA UI is referred to as "RAUX" internally in some technical documentation and code. For most users, it is presented as "GAIA UI".

For more details and setup instructions, see the [UI Documentation](docs/ui.md).

## Contents

### For Developers (SDK/Framework)
- [Using GAIA as an SDK](#using-gaia-as-an-sdk) - Build custom agents
- [SDK Reference](./docs/sdk/index.mdx) - Complete API documentation
- [Building from Source](#building-from-source)
- [Contributing](#contributing)

### For End Users (Application)
- [Installation](#installation) - Windows installer
- [Running the GAIA GUI](#running-the-gaia-gui)
- [Running the GAIA CLI](#running-the-gaia-cli)
- [Features](#features)

### Reference
- [System Requirements](#system-requirements)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contact](#contact)
- [License](#license)

# Getting Started Guide

## Prerequisites

**System Requirements:**

**Windows (Full Support):**
- **Windows 11 Home/Pro** 
- **16GB RAM minimum** (32GB recommended)
- **AMD Ryzen processor** (any generation)

**Linux:**
- **Ubuntu 20.04+** or **Debian 11+**
- **16GB RAM minimum** (32GB recommended)
- **x86_64 architecture**

**macOS:**
- **macOS 11 (Big Sur)** or newer
- **16GB RAM minimum** (32GB recommended)
- **Intel or Apple Silicon (M1/M2/M3)**

**Performance Tiers:**
- **Hybrid Mode** (NPU + iGPU): Requires AMD Ryzen AI 9 HX 300 series or newer
- **Vulkan Mode**: Older Ryzen processors use llama.cpp with Vulkan acceleration via Lemonade
- **CPU Mode**: Fallback for any system without GPU acceleration

## Installation

![image](./data/img/gaia-setup.png)

**Quick Install:**
1. Download the [latest release](https://github.com/amd/gaia/releases) installer from the "Assets" section
2. Unzip and double-click `gaia-windows-setup.exe`

   ⚠️ **NOTE**: If Windows shows a security warning, click *"More info"* then *"Run anyway"*

3. Follow the installer prompts (5-10 minutes depending on internet speed)
4. The installer includes:
   - GAIA CLI and GUI applications
   - Lemonade LLM server (handles all model acceleration automatically)
   - Required models and dependencies

## Verify Installation

Once installation completes, verify everything works:

1. Double-click the **GAIA-CLI** desktop icon
2. In the command prompt, run:
   ```bash
   gaia -v
   ```
3. You should see the GAIA version number displayed

## Your First GAIA Experience

**Option 1: Quick Chat (Recommended)**
```bash
gaia chat
```
Start an interactive conversation with the AI assistant.

**Option 2: Voice Conversation**
```bash
gaia talk
```
Have a voice-based conversation with AI (includes speech recognition and text-to-speech).

**Option 2b: Voice + Document Q&A**
```bash
gaia talk --index manual.pdf
```
Ask questions about your documents using voice - hands-free document assistance!

**Option 3: Web Interface**
Double-click the **GAIA-GUI** desktop icon to launch the modern web interface in your browser.

**Option 4: Direct Questions**
```bash
gaia llm "What can you help me with?"
```

The first time you run GAIA, it may take a few minutes to download and load models. Subsequent uses will be much faster.

### Command-Line Installation

If you prefer to use the command-line or for CI/CD environments, you can run the installer with parameters:

```
gaia-windows-setup.exe /S
```

Available parameters:
- `/S` - Silent installation (no UI)
- `/D=<path>` - Set installation directory (must be last parameter)

### Linux Installation

For Linux systems, GAIA provides both GUI and CLI support:

**GUI Installation:**
For GAIA UI (graphical interface) installation on Linux, see the [UI Documentation](docs/ui.md#ubuntu-deb) for detailed instructions including .deb package installation.

**CLI Installation from Source:**

**Prerequisites:**
- Python 3.10+ (3.12 recommended)
- git

**Installation Steps:**

1. Install uv (fast Python package manager):

   **Linux/macOS:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **Windows (PowerShell):**
   ```powershell
   irm https://astral.sh/uv/install.ps1 | iex
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/amd/gaia.git
   cd gaia
   ```

3. Create virtual environment and install GAIA:

   **Linux/macOS:**
   ```bash
   uv venv .venv --python 3.12
   source .venv/bin/activate
   uv pip install -e .
   ```

   **Windows (PowerShell):**
   ```powershell
   uv venv .venv --python 3.12
   .\.venv\Scripts\Activate.ps1
   uv pip install -e .
   ```

4. Install Lemonade server (for model serving):
   - Visit [lemonade-server.ai](https://www.lemonade-server.ai) for the latest release
   - Windows: Download and run `lemonade-server-minimal.msi`
   - Linux: Follow the documentation for source installation

5. Verify installation:
   ```bash
   gaia -v
   ```

**Note:** Both GUI (.deb packages) and CLI (source installation) are fully supported on Linux. 

## Uninstallation Steps

⚠️ **NOTE**: There is currently no automatic uninstaller available for GAIA, but one is coming soon. For now, you must manually remove GAIA from your system. Note that newer installations of GAIA will automatically remove older versions.

To completely uninstall GAIA from your system, follow these steps:

1. Close all running instances of GAIA (both CLI and GUI).

2. Remove the GAIA folder from AppData:
   1. Press `Win + R` to open the Run dialog
   2. Type `%localappdata%` and press Enter
   3. Find and delete the `GAIA` folder

3. Remove model files from the cache folder:
   1. Press `Win + R` to open the Run dialog
   2. Type `%userprofile%\.cache` and press Enter
   3. Delete any GAIA-related model folders (such as `huggingface` and `lemonade`)

4. Remove desktop shortcuts:
   1. Delete the GAIA-CLI and GAIA-GUI shortcuts from your desktop

## Running the GAIA GUI

Check your desktop for the GAIA-GUI icon and double-click it to launch the GUI. The first time you launch GAIA, it may take a few minutes to start. Subsequent launches will be faster. You may also need to download the latest LLM models from Hugging Face. GAIA will handle this automatically but may request a Hugging Face token for access. If you encounter any issues with model downloads or the GUI application, please refer to the [Troubleshooting](#troubleshooting) section or contact the [AMD GAIA team](mailto:gaia@amd.com).

## Installing Lemonade Server (Required for CLI Commands)

Most GAIA CLI commands require the Lemonade server to be running. If you installed GAIA with the installer, Lemonade server should already be included. However, you can also install it separately:

### Option 1: Standalone Installation
1. Visit [www.lemonade-server.ai](https://www.lemonade-server.ai) to download the latest release
2. Download and install `lemonade-server-minimal.msi` from the latest release
3. Ensure your system has the recommended Ryzen AI drivers installed (NPU Driver `32.0.203.237` or `32.0.203.240`)
4. Launch the server by double-clicking the `lemonade_server` desktop shortcut created during installation

### Option 2: Already Included with GAIA Installer
If you installed GAIA using our unified installer, Lemonade server is already included. Simply:
1. Double-click the GAIA-CLI desktop shortcut
2. GAIA will automatically start Lemonade Server when needed. You can also start it manually by running `lemonade-server serve`

**Note**: The Lemonade server provides OpenAI-compatible REST API endpoints and enables hybrid NPU/iGPU acceleration on Ryzen AI systems. For more details, see the [AMD Ryzen AI documentation](https://ryzenai.docs.amd.com/en/latest/llm/server_interface.html).

## Running the GAIA CLI

To quickly get started with GAIA via the command line, you can use the GAIA CLI (`gaia`) tool. Double click on the GAIA-CLI icon to launch the command-line shell with the GAIA environment activated, then run `gaia --help` for help details.

### Quick Start Examples

**Direct LLM Queries** (fastest option, no server management required):
```bash
gaia llm "What is artificial intelligence?"
gaia llm "Explain machine learning" --model Qwen2.5-0.5B-Instruct-CPU --max-tokens 200
```

**Interactive Chat Sessions**:
```bash
gaia chat                     # Start text chat with the AI assistant
gaia chat --index manual.pdf  # Chat with document Q&A support
```

**Single Prompts**:
```bash
gaia prompt "What's the weather?" --stats
gaia llm "Explain quantum computing"
```

**Voice Interaction**:
```bash
gaia talk  # Start voice-based conversation
```

**3D Scene Creation with Blender Agent**:
```bash
gaia blender                                    # Run all Blender examples
gaia blender --interactive                      # Interactive 3D scene creation
gaia blender --query "Create a red cube and blue sphere"  # Custom 3D scene query
gaia blender --example 2                        # Run specific example
```

### Available Commands

- `llm` - Direct LLM queries (requires Lemonade server)
- `prompt` - Send single message to an agent
- `chat` - Interactive text conversation
- `talk` - Voice-based conversation
- `code` - Python code assistant with analysis and generation
- `blender` - Create and modify 3D scenes using the Blender agent
- `jira` - Natural language interface for Atlassian tools
- `docker` - Natural language interface for Docker containerization
- `summarize` - Summarize meeting transcripts and emails
- `api` - Start GAIA API server for IDE integrations
- `mcp` - Start MCP bridge for external integrations
- `download` - Download models for GAIA agents
- `pull` - Download a specific model
- `stats` - View performance statistics
- `groundtruth` - Generate evaluation data with Claude
- `test` - Run audio/speech tests
- `youtube` - Download YouTube transcripts
- `kill` - Kill processes on specific ports

**Note**: Most commands require the Lemonade server. GAIA will automatically start Lemonade Server when needed. You can also start it manually by double-clicking the desktop shortcut or running `lemonade-server serve`.

**Blender Command**: The `blender` command additionally requires a Blender MCP server. See [CLI documentation](docs/cli.md#blender-command) for setup instructions.

For comprehensive information and examples, please refer to the [gaia documentation](docs/cli.md).

## Building from Source

To get started building from source, please follow the latest instructions [here](./docs/dev.md). These instructions will setup the [Onnx Runtime GenAI](https://github.com/microsoft/onnxruntime-genai) through the [Lemonade Server](https://lemonade-server.ai/) tool targeting the Ryzen AI SoC.


# Features

For a list of features and supported LLMs, please refer to the [Features](docs/features.md) page.

# Contributing

We welcome contributions from the community! GAIA is being transformed into a production-ready SDK for building AI agents.

## Ways to Contribute

### Build External Agents (Recommended)

**Build agents in your own repository:**

```bash
# Create your agent
gaia init my-agent --template document-chat  # (coming soon)
cd my-agent

# Develop and publish
pip install -e ".[dev]"
pytest tests/ -v
python -m build
twine upload dist/*

# Now anyone can: pip install my-agent
```

Benefits:
- Own your code and release cycle
- Use GAIA as a dependency
- Contribute to ecosystem without core changes

### Framework Contributions

**Priority contributions:**
- **Issue #1: DatabaseMixin** - SQLAlchemy integration for stateful agents
- **Issue #2: FileChangeHandler** - Extract file watching utility
- **Issue #4: Plugin Registry** - Entry point discovery system
- **Issue #13: `gaia init --claude`** - AI-assisted development
- See [GitHub Issues](https://github.com/amd/gaia/issues) for all open issues

### Documentation

- SDK examples and tutorials
- Agent development patterns
- API reference improvements

### Testing

- Framework test utilities
- Template testing
- Integration tests

## Contribution Guidelines

- Submit via Pull Request
- Follow code style (black, ruff)
- Add tests for new features
- Update documentation

For adding features to the GUI, see our [UI Development Guide](docs/ui.md).

# System Requirements

## Minimum Requirements:

- OS: Windows, Linux
- CPU: Any modern CPU, such as Ryzen 5700X or higher
- RAM: 16GB

## Minimally Recommended:

- OS: Windows, Linux
- CPU/GPU with NPU: AMD Ryzen AI 7 350
- RAM: 16GB+

## Ultra Performance:

- OS: Windows, Linux
- CPU/GPU with NPU: AMD Ryzen AI Max+ 395
- or if discrete GPU: any modern GPU with at least 16GB, such as Radeon RX 9070 XT
- RAM: 64GB+

---

GAIA with Ryzen AI Hybrid NPU/iGPU execution has been tested on the following system below. Any system that has the AMD Ryzen AI 9 300 series processor with NPU Driver 32.0.203.237 on Windows 11 or newer with minimum of 16GB of main memory should work. For more details on what is supported, see [here](https://www.amd.com/en/products/software/ryzen-ai-software.html#tabs-2733982b05-item-7720bb7a69-tab).

⚠️ **NOTE**:
- **Windows**: Full GUI and CLI support with installer
- **Linux**: Full GUI and CLI support via source installation
- **macOS**: CLI support via source installation (see [Development Guide](docs/dev.md))

GAIA has been tested on the following system:

- Systems: Asus ProArt PX13/P16, HP Omnibook with Ryzen AI 9 HX 370 series processor
- OS: Windows 11 Pro
- Processor: AMD Ryzen AI 9 HX 370 w/ Radeon 890M
- AMD Radeon 890M iGPU drivers: `32.0.12010.8007` and `32.0.12033.1030`
- AMD NPU drivers: `32.0.203.240` and newer
- AMD Adrenalin Software: Install the latest version from [AMD's official website](https://www.amd.com/en/products/software/adrenalin.html)
- Physical Memory: 32GB
- Recommended: AMD Ryzen AI 9 HX 370 with NPU Driver `32.0.203.240` and newer

**NOTE**: Use NPU Driver `32.0.203.240` and newer. You can check your driver version by going to *Device Manager -> Neural Processors -> NPU Compute Accelerator Device -> Right-Click Properties -> Driver Tab -> Driver Version*.


## Dependencies

The GAIA installer will automatically set up most dependencies, including:
- Python 3.12
- FFmpeg
- All required Python packages

**For development/source installations:**
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager (10-100x faster than pip)

# Troubleshooting

If you encounter issues with GAIA, please check the following common solutions:

## Driver Issues
- **NPU Driver Incompatibility**: For Hybrid mode, ensure you have NPU Driver `32.0.203.237` or `32.0.203.240`. Driver `32.0.203.242` may experience issues.
- **iGPU Driver Issues**: Make sure your AMD Radeon 890M iGPU drivers are `32.0.12010.8007` or `32.0.12033.1030`.
- **Driver Updates**: Install the latest AMD Adrenalin Software from [AMD's official website](https://www.amd.com/en/products/software/adrenalin.html).

## Installation Problems
- **Windows Security Warning**: If you get a Windows Security warning, click *"More info"* and then *"Run anyway"*.
- **Installation Fails**: Make sure you have administrator rights and sufficient disk space.
- **Previous Installation**: If prompted to delete an existing installation, it's recommended to allow this to avoid conflicts.

## Model Download Issues
- **Hugging Face Token**: If requested, provide a valid Hugging Face token to download models.
- **Slow Downloads**: Check your internet connection and be patient during the initial setup.

## Performance Problems
- **Disable Discrete GPUs**: When using Hybrid mode, disable any discrete third-party GPUs in Device Manager.
- **Low Memory**: Ensure you have at least 16GB of RAM (32GB recommended).

For additional troubleshooting assistance, please contact the [AMD GAIA team](mailto:gaia@amd.com).

# FAQ

For frequently asked questions, please refer to the [FAQ](docs/faq.md).

# Contact

Contact [AMD GAIA Team](mailto:gaia@amd.com) for any questions, feature requests, access or troubleshooting issues.

# License

[MIT License](./LICENSE.md)

Copyright(C) 2024-2025 Advanced Micro Devices, Inc. All rights reserved.
SPDX-License-Identifier: MIT