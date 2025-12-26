# Copyright(C) 2024-2025 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

# GAIA PyPI Publishing Guide

This guide explains how to build and publish the GAIA package to PyPI.

## Prerequisites

Install the required tools:

```bash
uv pip install twine
```

> **Note:** `uv build` is built into uv, no separate `build` package needed.

## Setting Up a PyPI Account

### Create an Account

1. **Production PyPI**: Go to [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. **Test PyPI** (recommended for testing): Go to [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)

Fill in the required information:
- Username
- Email address
- Password (strong password required)

### Enable Two-Factor Authentication (Required)

PyPI requires 2FA for all accounts publishing packages:

1. Log in to your PyPI account
2. Go to **Account Settings** → **Two factor authentication**
3. Choose an authentication method:
   - **TOTP (Time-based One-Time Password)**: Use an authenticator app (Google Authenticator, Authy, etc.)
   - **Security Key**: Use a hardware security key (YubiKey, etc.)
4. Follow the setup wizard and save your recovery codes securely

### Generate an API Token

API tokens are the recommended authentication method for uploads:

1. Go to **Account Settings** → **API tokens**
2. Click **Add API token**
3. Choose a token name (e.g., "gaia-uploads")
4. Set scope:
   - **Entire account**: Can upload to any project you own
   - **Project-specific**: Limited to a specific project (more secure, but only available after first upload)
5. Click **Create token**
6. **Copy the token immediately** - it won't be shown again
7. Store the token securely (password manager, environment variable, or `.pypirc`)

## Registering the Package on PyPI

PyPI no longer supports pre-registering package names. The package name is claimed when you **upload your first release**.

### Check Name Availability

Before your first upload, verify the package name isn't taken:

1. Search on [https://pypi.org/search/](https://pypi.org/search/) for "amd-gaia"
2. Or try to access `https://pypi.org/project/amd-gaia/` directly

### Reserve the Name (First Upload)

The package name is claimed with your first successful upload:

```bash
# Build the package first
uv build

# Upload to claim the name
twine upload dist/*
```

Once uploaded, you become the **Owner** of that package name on PyPI.

### Managing Project Permissions

After the first upload, you can add collaborators:

1. Go to your project page on PyPI
2. Click **Manage** → **Collaborators**
3. Add users by their PyPI username with roles:
   - **Owner**: Full control (add/remove users, delete project)
   - **Maintainer**: Can upload new releases

### Organization Accounts (Optional)

For team projects, consider creating a PyPI Organization:

1. Go to **Account Settings** → **Your organizations**
2. Create a new organization
3. Transfer project ownership to the organization
4. Add team members to the organization with appropriate roles

## Publishing Workflow

> **IMPORTANT: PyPI does not allow overwriting existing versions.** Once a version is uploaded, that exact filename can never be uploaded again. This is a security feature to prevent supply chain attacks. Always bump the version number for new releases.

### Step 1: Update Version

Edit `src/gaia/version.py` and bump the version number:

```python
__version__ = "0.14.2"  # Bump as needed
```

### Step 2: Clean and Build the Package

> **CRITICAL:** Always clean the `dist/` directory before building. If old wheel files remain, `twine upload dist/*` will attempt to upload them alongside the new version, causing "File already exists" errors.

```bash
# REQUIRED: Clean previous builds first
rm -rf dist/ build/ *.egg-info

# Verify dist/ is empty (should show nothing or "No such file")
ls dist/

# Build source distribution and wheel
uv build

# Verify only ONE version exists in dist/
ls dist/
# Should show ONLY:
#   amd_gaia-X.Y.Z.tar.gz
#   amd_gaia-X.Y.Z-py3-none-any.whl
```

This creates files in `dist/`:
- `amd_gaia-X.Y.Z.tar.gz` (source distribution)
- `amd_gaia-X.Y.Z-py3-none-any.whl` (wheel)

### Step 3: Verify the Package

```bash
# Check package metadata
twine check dist/*

# Test install locally
uv pip install dist/amd_gaia-*.whl
```

## Testing with External Projects Locally

Before publishing to PyPI, you should test the GAIA wheel with external projects (like third-party agents) to ensure everything works correctly.

### Scenario: Testing GAIA with an External Agent

You're developing both:
- **GAIA framework** in `/path/to/gaia/`
- **Your Agent** in `/path/to/your-agent/`

You want to test if your agent works with your local GAIA changes before publishing.

### Option A: Install Local Wheel (Recommended for Testing)

**Step 1: Build GAIA wheel**

From the GAIA repository:

```bash
cd /path/to/gaia

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build fresh wheel
uv build
```

This creates `dist/amd_gaia-X.Y.Z-py3-none-any.whl` (version varies).

**Step 2: Install wheel in external project**

From your external project:

```bash
cd /path/to/your-agent

# Create/activate virtual environment (recommended)
uv venv .venv
source .venv/bin/activate       # macOS/Linux
# .\.venv\Scripts\activate      # Windows

# Install the local GAIA wheel
uv pip install /path/to/gaia/dist/amd_gaia-X.Y.Z-py3-none-any.whl

# Verify installation
python -c "from gaia import Agent, tool; print('Success!')"
gaia --version
```

**Step 3: Install your agent**

```bash
# Install your agent in development mode
uv pip install -e ".[dev]"

# Test it works
gaia list-agents
# Should show your agent

pytest tests/ -v
# All tests should pass
```

**Step 4: Iterate on GAIA changes**

When you make changes to GAIA:

```bash
# Terminal 1: GAIA repository
cd /path/to/gaia

# Make your changes to src/gaia/...
# Edit files, add features, fix bugs

# Rebuild wheel
rm -rf dist/
uv build

# Terminal 2: External project
cd /path/to/your-agent

# Reinstall updated GAIA wheel
uv pip install --force-reinstall /path/to/gaia/dist/amd_gaia-*.whl

# Test your agent again
pytest tests/ -v
```

### Option B: Editable Install (For Active Development)

Use this when you're **actively developing GAIA** alongside your external project and want immediate changes.

**Setup:**

```bash
cd /path/to/your-agent

# Install GAIA in editable mode (not from wheel)
uv pip install -e /path/to/gaia

# Install your agent in editable mode
uv pip install -e ".[dev]"
```

**Benefits:**
- Changes to GAIA code are **immediately reflected** (no rebuild needed)
- Fast iteration - edit GAIA, test immediately
- Good for debugging across both projects

**Drawbacks:**
- Not the same as PyPI install (won't catch packaging issues)
- Harder to switch between GAIA versions
- May have import path issues on Windows

**When to use:**
- You're fixing a bug in GAIA that affects your agent
- You're adding a new GAIA feature and testing it simultaneously
- You're doing active development on both projects

### Option C: Test in Clean Environment

Before final release, test in a completely clean environment:

```bash
# Create fresh virtual environment
cd /path/to/your-agent
uv venv test-env
source test-env/bin/activate    # macOS/Linux
# .\test-env\Scripts\activate   # Windows

# Install ONLY from local wheel (no editable installs)
uv pip install /path/to/gaia/dist/amd_gaia-X.Y.Z-py3-none-any.whl

# Install your agent
uv pip install .

# Run full test suite
pytest tests/ -v --cov

# Test CLI commands
gaia --help
gaia list-agents

# If everything works, GAIA is ready to publish!
```

### Workflow Comparison

| Workflow | Speed | Accuracy | Use Case |
|----------|-------|----------|----------|
| **Wheel Install** | Medium | High | Pre-release testing |
| **Editable Install** | Fast | Low | Active development |
| **Clean Environment** | Slow | Highest | Final validation |

### Complete Development Workflow

```bash
# 1. Develop GAIA feature
cd /path/to/gaia
# Edit src/gaia/agents/base/...
# Add new methods

# 2. Use editable install for rapid testing
cd /path/to/your-agent
uv pip install -e /path/to/gaia
pytest tests/ -v  # Test immediately

# 3. Once feature is stable, test with wheel
cd /path/to/gaia
uv build
cd /path/to/your-agent
uv pip install --force-reinstall /path/to/gaia/dist/amd_gaia-*.whl
pytest tests/ -v  # Full test suite

# 4. Final validation in clean environment
uv venv final-test
source final-test/bin/activate
uv pip install /path/to/gaia/dist/amd_gaia-*.whl
uv pip install .
pytest tests/ -v --cov

# 5. If all tests pass, publish to PyPI
deactivate
cd /path/to/gaia
twine upload dist/*
```

### Troubleshooting

**Problem: "File already exists" error when uploading to PyPI**

```
ERROR    HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/
         File already exists ('amd_gaia-0.14.1-py3-none-any.whl', ...)
```

This happens when:
1. **Old wheel files in `dist/`**: You rebuilt without cleaning, so both old and new versions exist
2. **Version not bumped**: You're trying to re-upload an already published version

**Solution:**

```bash
# Check what's in dist/ - look for multiple versions
ls dist/
# Bad: amd_gaia-0.14.1-py3-none-any.whl AND amd_gaia-0.14.2-py3-none-any.whl
# Good: Only amd_gaia-0.14.2-py3-none-any.whl

# Clean and rebuild
rm -rf dist/ build/ *.egg-info
uv build

# Verify only one version
ls dist/

# Now upload
twine upload dist/*
```

If the version was already published, you MUST bump the version number in `src/gaia/version.py` and rebuild. PyPI does not allow overwriting existing versions.

---

**Problem: "Module not found" after installing wheel**

```bash
# Check wheel contents
unzip -l dist/amd_gaia-*.whl | grep -i "module_name"

# Verify installation location
uv pip show amd-gaia
# Check Location: and Files:

# Reinstall with verbose output
uv pip install --force-reinstall -v /path/to/gaia/dist/amd_gaia-*.whl
```

**Problem: Old version still installed**

```bash
# Uninstall completely
uv pip uninstall amd-gaia -y

# Check no remnants
uv pip show amd-gaia
# Should show nothing

# Reinstall
uv pip install /path/to/gaia/dist/amd_gaia-*.whl
```

**Problem: Changes not reflected**

```bash
# If using editable install, Python may cache imports
# Restart Python interpreter or:
import importlib
import gaia
importlib.reload(gaia)

# If using wheel install, ensure you rebuilt:
cd /path/to/gaia
rm -rf dist/
uv build
uv pip install --force-reinstall dist/amd_gaia-*.whl
```

**Problem: Dependency conflicts**

```bash
# Show full dependency tree
uv pip install pipdeptree
pipdeptree -p amd-gaia

# Create clean environment
uv venv clean-test
source clean-test/bin/activate
uv pip install /path/to/gaia/dist/amd_gaia-*.whl
# See what gets installed
```

### Best Practices

1. **Use virtual environments** - Always test in isolated environments
2. **Version your wheels** - Keep old wheels for regression testing
3. **Test with requirements.txt** - Ensure pinned dependencies work
4. **Check package size** - Ensure no unnecessary files in wheel
5. **Validate entry points** - Test CLI commands work from wheel install
6. **Cross-platform testing** - Test wheel on Windows, macOS, Linux if possible

```bash
# Check wheel size
ls -lh dist/*.whl

# List wheel contents
unzip -l dist/amd_gaia-*.whl | head -20

# Test entry points
uv pip install dist/amd_gaia-*.whl
which gaia  # Should point to venv/bin/gaia or venv/Scripts/gaia
gaia --help  # Should work
gaia list-agents  # Should show built-in agents
```

### Step 4: Publish to Test PyPI (Recommended First)

```bash
twine upload --repository testpypi dist/*
```

Test the installation:

```bash
# Base package
uv pip install --index-url https://test.pypi.org/simple/ amd-gaia

# With extras
uv pip install --index-url https://test.pypi.org/simple/ 'amd-gaia[api,rag]'
```

### Step 5: Publish to Production PyPI

```bash
twine upload dist/*
```

You'll need PyPI credentials (username/API token).

## Authentication Options

### Option A: API Token (Recommended)

```bash
twine upload -u __token__ -p pypi-YOUR_API_TOKEN dist/*
```

### Option B: `.pypirc` Configuration File

Create `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN

[testpypi]
username = __token__
password = pypi-YOUR_TEST_API_TOKEN
```

Then simply run:

```bash
twine upload dist/*
```

## Important Notes

1. **Public vs Private Repo**: GAIA uses a private-to-public sync via `release.py`. PyPI packages should only be published from the **public repo** (`amd/gaia`) after running the release script.

2. **Version Format**: Follow semantic versioning (MAJOR.MINOR.PATCH).

3. **Package Name**: The PyPI package is `amd-gaia` (import name remains `gaia`).

4. **Dependencies**: All dependencies are defined in `setup.py` under `install_requires` and `extras_require`.

## Optional Dependencies (Extras)

GAIA packages optional features as extras to keep the base install lightweight. Users install only what they need.

### Available Extras

From `setup.py`:

```python
extras_require={
    "api": ["fastapi>=0.115.0", "uvicorn>=0.32.0"],
    "rag": ["pypdf", "pymupdf>=1.24.0", ...],
    "audio": ["torch>=2.0.0", "openai-whisper", ...],
    "talk": ["pyaudio", "openai-whisper", "kokoro>=0.3.1", ...],
    "blender": ["bpy"],
    "mcp": ["mcp>=1.1.0", "starlette", "uvicorn"],
    "dev": ["pytest", "black", "pylint", ...],
    "eval": ["anthropic", "bs4", "scikit-learn", ...],
    "youtube": ["llama-index-readers-youtube-transcript"],
}
```

### Installing with Extras

**Single extra:**
```bash
pip install amd-gaia[api]
```

**Multiple extras:**
```bash
pip install amd-gaia[api,rag]
```

**Development install with extras:**
```bash
pip install -e ".[api,rag,dev]"
```

### Common Combinations

| Use Case | Extras | Example |
|----------|--------|---------|
| **EMR Medical Intake Agent** | `api,rag` | `pip install amd-gaia[api,rag]` |
| Document Q&A (Chat Agent) | `rag` | `pip install amd-gaia[rag]` |
| Voice Interface (Talk) | `talk` | `pip install amd-gaia[talk]` |
| Web Dashboards | `api` | `pip install amd-gaia[api]` |
| MCP Server | `mcp` | `pip install amd-gaia[mcp]` |
| Full Development | `dev,api,rag` | `pip install -e ".[dev,api,rag]"` |

**Note:** The EMR agent (`gaia-emr`) requires both `api` (for FastAPI dashboard) and `rag` (for PDF processing with PyMuPDF).

### Testing Extras in Local Wheels

When testing local changes with extras:

```bash
# Build wheel
cd /path/to/gaia
rm -rf dist/
uv build

# Install with extras
cd /path/to/your-project
uv pip install '/path/to/gaia/dist/amd_gaia-*.whl[api,rag]'

# Verify extras installed
python -c "import fastapi; import pymupdf; print('Extras OK')"
```

**Important:** Quote the path when using brackets on bash/zsh to prevent glob expansion.

## Quick Reference

| Command | Description |
|---------|-------------|
| `uv build` | Build the package |
| `twine check dist/*` | Verify package metadata |
| `twine upload --repository testpypi dist/*` | Upload to Test PyPI |
| `twine upload dist/*` | Upload to Production PyPI |
| `pip install amd-gaia` | Install base package |
| `pip install amd-gaia[api,rag]` | Install with extras |
| `pip install -e ".[dev,api,rag]"` | Editable install with extras |
