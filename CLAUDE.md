# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GAIA (Generative AI Is Awesome) is AMD's open-source framework for running generative AI applications locally on AMD hardware, with specialized optimizations for Ryzen AI processors with NPU support.


## Development Environment

### Recent Code Agent Improvements (2024-12-01)
- **Architectural Planning**: Creates detailed PLAN.md with project structure before implementation
- **GAIA.md Support**: Automatically reads project context from GAIA.md and includes in system prompt
- **Project Initialization**: `gaia code /init` analyzes existing codebase to generate GAIA.md
- **Dynamic Project Generation**: Intelligently creates folder structures based on project type (game, API, library)
- **Enhanced File I/O**: Added markdown support and project structure creation tools
- **Code Quality**: Fixed all pylint warnings and integrated Black formatting
- **Generic Implementation**: Removed hardcoded examples - now generates appropriate code for ANY Python project

### Code Agent Key Capabilities
The CodeAgent provides comprehensive Python development support with over 30 specialized tools:

- **Architectural Planning**: Creates PLAN.md with detailed project architecture before coding
- **Project Context**: Reads GAIA.md for project-specific guidance (run `gaia code /init` to create)
- **Workflow Planning**: Analyzes complex requirements and creates multi-step execution plans
- **Code Generation**: Creates functions, classes, and tests with proper structure and documentation
- **Project Scaffolding**: Generates complete project structures with appropriate folder hierarchy
- **Test Generation**: Automatically generates unit tests from existing source code
- **Quality Assurance**: Runs pylint and Black, automatically fixing issues
- **Error Recovery**: Iteratively fixes syntax, runtime, and linting errors
- **File Management**: All generated code is automatically saved with appropriate naming
- **Diff Support**: Generates and applies unified diffs (Git-style)
- **Comprehensive Tools**: 30+ tools including file operations, code analysis, project management, and error fixing

## File Headers

**IMPORTANT: All new files created in this project MUST start with the following copyright header (using appropriate comment syntax for the file type):**

```
Copyright(C) 2024-2025 Advanced Micro Devices, Inc. All rights reserved.
SPDX-License-Identifier: MIT
```

## Documentation

**See "Documentation Index" section below for complete list of available documentation.**

### GAIA + RAUX Integration

GAIA works with RAUX (Electron-based desktop app) for enhanced UI and installation management. See [`docs/ui.md`](docs/ui.md) and [`docs/installer.md`](docs/installer.md) for details.

## Version Control Guidelines

### Repository Structure

This is the **gaia-pirate** repository (`aigdat/gaia`), the private repository where all GAIA development occurs. There are two related repositories:

1. **gaia-pirate** (`aigdat/gaia`) - **This repository** - Private development repository and single source of truth
2. **gaia-public** (`github.com/amd/gaia`) - Public open-source repository

**Development Workflow:**
- All development work happens in this private repository (gaia-pirate)
- **Claude will NEVER commit to the public repository** - releases are synced manually using `release.py`
- The `release.py` script filters out internal/NDA content based on an exclude list
- Files in the `./nda` directory are automatically excluded from public releases
- External contributions (issues/PRs) come through the public repository
- External contributions are manually reviewed and merged back into this private repository
- Legal review happens during the manual release process before PRs are completed in the public repo

See [`nda/docs/release.md`](nda/docs/release.md) for detailed release process documentation.

### IMPORTANT: Never Commit Changes
**NEVER commit changes to the repository unless explicitly requested by the user.** The user will decide when and what to commit. This prevents unwanted changes from being added to the repository history.

### Branch Management
- Main branch: `main`
- Feature branches: Use descriptive names (e.g., `kalin/mcp`, `feature/new-agent`)
- Always check current branch status before making changes
- Use pull requests for merging changes to main

## Testing Philosophy

### IMPORTANT: Always Test the CLI
When writing tests or CI/CD workflows, **ALWAYS test the actual CLI commands** that users will run. Never bypass the CLI by calling Python modules directly unless absolutely necessary for debugging.

**When testing GAIA features during development:**
- Always use the `gaia` CLI command, not Python module imports
- Test the exact commands that users will use in production
- This ensures the CLI interface, argument parsing, and module integration all work correctly

**Good:**
```bash
gaia mcp start --background
gaia mcp status
gaia mcp stop
```

**Bad (avoid unless debugging):**
```bash
python -m gaia.mcp.mcp_bridge
```

This ensures:
- CLI commands work as expected for end users
- Integration between CLI and modules is properly tested
- Command-line argument parsing is validated
- User experience matches test coverage

## Development Workflow

### Setup and Installation

**See:** [`docs/dev.md`](docs/dev.md) for complete development setup instructions.

Quick reference:
```bash
conda create -n gaiaenv python=3.10 -y
conda activate gaiaenv
pip install -e .[talk,dev,rag]
```

### Testing

**See:** [`docs/dev.md`](docs/dev.md) for comprehensive testing guide.

Quick reference:
```bash
conda activate gaiaenv
python -m pytest tests/
.\util\lint.ps1  # Run all linting checks
```

### Linting and Formatting

**See:** [`docs/dev.md`](docs/dev.md) for linting and formatting guidelines.

Quick reference:
```bash
.\util\lint.ps1           # Run all quality checks
.\util\lint.ps1 -RunBlack -Fix  # Auto-fix formatting
```

### Running GAIA Features

**See feature-specific documentation:**
- CLI commands: [`docs/cli.md`](docs/cli.md)
- Chat: [`docs/chat.md`](docs/chat.md)
- Code Agent: [`docs/code.md`](docs/code.md)
- Talk (Voice): [`docs/talk.md`](docs/talk.md)
- Blender: [`docs/blender.md`](docs/blender.md)
- Jira: [`docs/jira.md`](docs/jira.md)
- MCP: [`docs/mcp.md`](docs/mcp.md)

## Project Structure

```
gaia/
├── src/gaia/           # Main source code
│   ├── agents/         # Agent implementations
│   │   ├── base/       # Base agent framework
│   │   │   ├── agent.py        # Base Agent class with state management
│   │   │   └── console.py      # Console-based agent interface
│   │   ├── blender/    # Blender 3D agent
│   │   │   ├── agent.py        # Blender agent implementation
│   │   │   └── app.py          # Blender agent entry point
│   │   ├── code/       # Code development agent
│   │   │   ├── agent.py        # Autonomous coding workflow
│   │   │   ├── file_io_tools.py # File operations and markdown support
│   │   │   └── app.py          # CLI entry point
│   │   │       # Key Features:
│   │   │       # - Architectural planning with PLAN.md generation
│   │   │       # - GAIA.md context awareness (auto-loads project context)
│   │   │       # - Project initialization with `gaia code /init`
│   │   │       # - Dynamic project scaffolding based on type (game/API/library)
│   │   │       # - Complete folder structure generation
│   │   │       # - Code generation with automatic file saving
│   │   │       # - Automatic unit test creation from source code
│   │   │       # - Linting with pylint and auto-fix
│   │   │       # - Black formatting with correction
│   │   │       # - Iterative error correction
│   │   │       # - Markdown file support for documentation
│   │   └── jira/       # Jira integration agent
│   │       ├── agent.py        # Jira agent with NLP capabilities
│   │       └── app.py          # Jira agent entry point
│   ├── apps/           # Standalone applications
│   │   ├── _shared/    # Shared utilities for app development
│   │   │   └── dev-server.js   # Development server for browser mode
│   │   ├── example/    # Example MCP integration app (demo/template)
│   │   │   └── webui/          # Electron app structure
│   │   ├── jira/       # Jira app with natural language interface
│   │   │   └── webui/          # Electron app structure
│   │   ├── llm/        # Direct LLM interface
│   │   │   └── app.py          # LLM query application
│   │   └── summarize/  # Document summarization
│   │       └── app.py          # Summarization application
│   ├── audio/          # Audio processing (ASR/TTS)
│   │   ├── asr.py              # Speech recognition (Whisper)
│   │   └── tts.py              # Text-to-speech (Kokoro)
│   ├── chat/           # Chat interface and SDK
│   │   ├── app.py              # Interactive chat application
│   │   ├── sdk.py              # Chat SDK with session management
│   │   └── prompts.py          # System prompts and templates
│   ├── eval/           # Evaluation framework
│   │   ├── groundtruth.py      # Ground truth generation
│   │   └── experiment.py       # Batch experiment runner
│   ├── llm/            # LLM backend clients
│   │   ├── llm_client.py       # Base LLM client interface
│   │   └── lemonade_client.py  # Lemonade server integration
│   ├── mcp/            # Model Context Protocol
│   │   ├── mcp_bridge.py       # HTTP-native MCP server
│   │   ├── mcp.json            # MCP configuration
│   │   ├── atlassian_mcp.py   # Atlassian services wrapper
│   │   └── blender_mcp_server.py # Blender MCP integration
│   ├── talk/           # Voice interaction
│   │   ├── app.py              # Voice interaction application
│   │   └── sdk.py              # Talk SDK for voice processing
│   ├── cli.py          # Main CLI entry point
│   ├── logger.py       # Logging configuration
│   ├── util.py         # Utility functions
│   └── version.py      # Version information
├── tests/              # Test suite
│   ├── unit/           # Unit tests
│   │   ├── test_asr.py         # ASR tests
│   │   ├── test_tts.py         # TTS tests
│   │   └── test_llm.py         # LLM client tests
│   ├── mcp/            # MCP integration tests
│   │   ├── test_mcp_simple.py  # Basic MCP tests
│   │   ├── test_mcp_http_validation.py # HTTP validation
│   │   ├── test_mcp_jira.py    # Jira MCP tests
│   │   └── test_mcp_integration.py # Integration tests
│   ├── test_chat_sdk.py        # Chat SDK tests
│   ├── test_eval.py            # Evaluation framework tests
│   ├── test_jira.py            # Comprehensive Jira tests
│   ├── test_lemonade_client.py # Lemonade client tests
│   ├── test_summarizer.py      # Summarizer tests
│   └── conftest.py             # Pytest configuration
├── docs/               # Documentation
│   ├── apps/           # App-specific documentation
│   │   ├── dev.md              # App development guide
│   │   ├── jira.md             # Jira app documentation
│   │   └── README.md           # Desktop applications overview
│   ├── cli.md                  # CLI reference guide
│   ├── code.md                 # Code agent guide
│   ├── mcp.md                  # MCP server documentation
│   ├── n8n.md                  # n8n workflow integration
│   ├── jira.md                 # Jira agent guide
│   ├── blender.md              # Blender agent guide
│   ├── chat.md                 # Chat interface guide
│   ├── talk.md                 # Voice interaction guide
│   ├── eval.md                 # Evaluation framework guide
│   ├── dev.md                  # Development guide
│   ├── features.md             # Feature overview
│   ├── ui.md                   # Web UI documentation
│   └── faq.md                  # Troubleshooting guide
├── installer/          # NSIS installer scripts
│   └── installer.nsi           # Windows installer script
├── workshop/           # Tutorial materials
│   └── blender.ipynb           # Blender workshop notebook
├── util/               # Utility scripts
│   └── lint.ps1                # PowerShell linting script
├── .github/workflows/  # CI/CD pipelines
│   ├── lint.yml                # Code quality checks
│   ├── test_mcp.yml            # MCP test workflow
│   └── build_installer.yml     # Installer build workflow
├── setup.py            # Package setup configuration
├── pyproject.toml      # Project metadata
├── CLAUDE.md           # Claude Code guidance (this file)
├── README.md           # Project readme
├── CONTRIBUTING.md     # Contribution guidelines
├── LICENSE.md          # MIT license
├── .env.example        # Environment variables template
├── run_jira_tests.py   # Jira test runner
└── validate_mcp.py     # MCP protocol validator
```

## Architecture

### Core Components

1. **Agent System** (`src/gaia/agents/`): WebSocket-based agents with specialized capabilities
   - Base `Agent` class (`src/gaia/agents/base/agent.py`) handles communication protocol, tool execution, and conversation management
   - State management: PLANNING → EXECUTING_PLAN → COMPLETION with error recovery
   - Tool registry system for domain-specific functionality
   - Current agents:
     - **Llm**: Direct LLM queries
     - **Code**: Autonomous Python development with comprehensive workflow:
       - Creates multi-step plans for complex tasks
       - Generates code from natural language descriptions
       - Automatically writes generated code to files (functions, classes, tests)
       - Creates unit tests with proper naming (test_[module].py)
       - Runs pylint and automatically fixes linting errors
       - Applies Black formatting with auto-fix capability
       - Executes code and fixes runtime errors iteratively
       - Supports file operations with unified diff generation
       - Returns file paths instead of code content for better usability
     - **Blender**: 3D content creation
     - **Jira**: Issue management with automatic configuration discovery
   - Console-based agent interface (`src/gaia/agents/base/console.py`) for interactive sessions

2. **LLM Backend Layer** (`src/gaia/llm/`): Multiple backend support
   - `lemonade_client.py`: AMD-optimized ONNX Runtime GenAI backend via Lemonade Server
   - Uses Lemonade Server for running LLM models with hardware optimization
   - OpenAI-compatible API with streaming support
   - Automatic server management and health checking

3. **Evaluation Framework** (`src/gaia/eval/`): Comprehensive testing and evaluation
   - Ground truth generation with Claude AI integration
   - Batch experiment execution with multiple models
   - Transcript analysis and summarization evaluation
   - Performance metrics and statistical analysis

4. **Audio Pipeline** (`src/gaia/audio/`): Complete audio processing
   - Whisper ASR for speech recognition
   - Kokoro TTS for text-to-speech
   - Audio recording and playback capabilities

5. **MCP Integration** (`src/gaia/mcp/`): Model Context Protocol support
   - Generic MCP bridge server for external client integration
   - Atlassian wrapper for Jira, Confluence, and Compass integration
   - Blender MCP server for 3D modeling integration
   - WebSocket-based communication following MCP specification
   - Support for tools, resources, prompts, and streaming responses
   - Background process management with status tracking

6. **Applications** (`src/gaia/apps/`): Standalone application modules
   - Shared development utilities (`_shared/`) for browser and Electron modes
   - Example app template for MCP integration demos
   - Jira app with natural language interface for issue management
   - Document summarization with multiple output styles and formats
   - PDF formatting and HTML viewing capabilities
   - Configurable summarization templates and prompts

6. **RAG System** (`src/gaia/rag/`): Document retrieval and Q&A
   - PDF text extraction and chunking with overlap
   - Vector embeddings using sentence-transformers
   - FAISS similarity search for document retrieval
   - Integration with Chat SDK for context-aware conversations
   - Caching system for performance optimization

### Key Architecture Patterns

- **Agent Pattern**: All domain-specific functionality implemented as agents inheriting from base `Agent` class
- **Tool Registry**: Dynamic tool registration system allowing agents to expose domain-specific capabilities
- **Streaming Support**: Real-time response streaming throughout the system
- **Server Management**: Automatic startup, health checking, and cleanup of backend servers
- **Error Recovery**: Built-in error handling and recovery mechanisms in agent conversations
- **SDK Integration**: Chat and Talk SDKs (`sdk.py` files) provide programmatic interfaces
- **Configuration Management**: Environment-based configuration with `.env` file support
- **Cross-platform Support**: Windows and Linux compatibility with platform-specific optimizations

### Backend Architecture

GAIA uses Lemonade Server as the LLM backend, which provides hardware-optimized model execution on available AMD hardware including NPU and iGPU on supported Ryzen AI systems.

The system uses different models for different agents:
- **Default model**: Qwen2.5-0.5B-Instruct-CPU for general agent tasks
- **Coding tasks**: Qwen3-Coder-30B-A3B-Instruct-GGUF for code-related operations
- **Jira Agent**: Uses Qwen3-Coder-30B-A3B-Instruct-GGUF by default for reliable JSON parsing and complex operations

### Testing Architecture

Tests are organized by component:
- `tests/unit/`: Unit tests for individual modules (ASR, TTS, LLM)
- `tests/test_*.py`: Integration tests
- `tests/mcp/`: MCP-specific integration and validation tests
- `conftest.py`: Shared test fixtures with `--hybrid` configuration support
- Agent-specific tests in `src/gaia/agents/*/tests/`
- Test utilities: `run_jira_tests.py` for comprehensive Jira testing
- Validation scripts: `validate_mcp.py` for MCP protocol compliance

When adding new agents, follow the pattern in existing agents with separate `app.py` and agent implementation files.

## RAG (Retrieval-Augmented Generation)

RAG enables document-based Q&A by integrating with the chat command.

**For complete RAG documentation including:**
- Installation and setup
- CLI usage examples
- Python SDK API reference
- Configuration options
- Troubleshooting guide
- Advanced usage patterns

**See:** [`docs/chat.md#document-qa-with-rag`](docs/chat.md#document-qa-with-rag)

### CI/CD Pipeline

GitHub Actions workflows are configured for:
- **Linting**: `lint.yml` - Code quality checks
- **Testing**: Multiple test workflows for different components
  - `test_gaia_cli.yml`, `test_gaia_cli_linux.yml`, `test_gaia_cli_windows.yml`
  - `test_mcp.yml` - MCP integration tests
  - `test_chat_sdk.yml` - Chat SDK tests
  - `test_eval.yml` - Evaluation framework tests
- **Building**: `build_installer.yml` - NSIS installer creation
- **Publishing**: `publish_installer.yml` - Release distribution
- **Hybrid Testing**: `local_hybrid_tests.yml` - Local and cloud model testing

## Documentation Index

**User Documentation:**
- [`docs/cli.md`](docs/cli.md) - CLI commands and usage
- [`docs/chat.md`](docs/chat.md) - Chat and RAG (document Q&A)
- [`docs/talk.md`](docs/talk.md) - Voice interaction
- [`docs/code.md`](docs/code.md) - Code Agent
- [`docs/blender.md`](docs/blender.md) - Blender 3D agent
- [`docs/jira.md`](docs/jira.md) - Jira integration
- [`docs/features.md`](docs/features.md) - Feature overview
- [`docs/faq.md`](docs/faq.md) - Troubleshooting

**Developer Documentation:**
- [`docs/dev.md`](docs/dev.md) - Development setup and testing
- [`docs/apps/dev.md`](docs/apps/dev.md) - Building desktop apps
- [`docs/mcp.md`](docs/mcp.md) - MCP server development
- [`docs/eval.md`](docs/eval.md) - Evaluation framework
- [`CONTRIBUTING.md`](CONTRIBUTING.md) - Contribution guidelines

**Platform-Specific:**
- [`docs/installer.md`](docs/installer.md) - Windows installer
- [`docs/ui.md`](docs/ui.md) - Web UI deployment

## File Path Rules (Workaround for Claude Code v1.0.111 Bug)
- When reading or editing a file, **ALWAYS use relative paths.**
- Example: `./src/components/Component.tsx` ✅
- **DO NOT use absolute paths.**
- Example: `C:/Users/user/project/src/components/Component.tsx` ❌
- Reason: This is a workaround for a known bug in Claude Code v1.0.111 (GitHub Issue
- when you invoke a particular proactive agent from @.claude\agents\, make sure to indicate what agent you are invoking in your response back to the user