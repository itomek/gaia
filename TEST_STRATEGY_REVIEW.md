# GAIA Test Strategy Review

> **Date:** 2026-01-15
> **Repository:** amd/gaia (gaia-pirate)
> **Reviewer:** Claude Code Analysis
> **Methodology:** Actual `pytest --cov` execution + code analysis

---

## Executive Summary

The GAIA test suite has **solid foundations** but suffers from **organizational inconsistencies**, **significant coverage gaps**, and **mixed test classifications**. This review identifies issues and provides actionable recommendations for cleanup, consolidation, and alignment with proper testing patterns.

**Key Findings (MEASURED):**
- **141 source modules** (excluding `__init__.py`) with **9% statement coverage**
- **22,660 total statements**, **20,653 not covered** by unit tests
- **218 unit tests pass**, 13 skipped (hardware-dependent)
- **17 agent-related test files** to be migrated to `amd/gaia-agents`
- Inconsistent frameworks (unittest.TestCase vs pytest)
- Hardcoded ports (8000, 8080, 8765) prevent parallel test execution
- Global `_TOOL_REGISTRY` pollution (13 manual `.clear()` calls across tests)

---

## 1. Current Test Structure

### Directory Layout

```
tests/
├── conftest.py                    # Global fixtures (4 fixtures)
├── [17 root-level test files]     # Mixed unit/integration (~15K lines)
├── unit/                          # 9 files (~4.3K lines)
├── integration/                   # 2 files
├── mcp/                           # 5 files (MCP protocol tests)
└── electron/                      # 3 JavaScript files (Electron app)

src/gaia/agents/blender/tests/     # 3 files (embedded in source)
```

### Test Statistics (MEASURED)

| Metric | Value |
|--------|-------|
| Total Python test files | 36 |
| Unit tests collected | 231 |
| Unit tests passed | 218 |
| Unit tests skipped | 13 |
| Source modules (non-init) | 141 |
| Total statements | 22,660 |
| Statements covered | 2,007 |
| **Measured unit coverage** | **9%** |

---

## 2. Coverage Analysis (MEASURED via pytest-cov)

### Modules WITH Good Coverage (>50%)

| Module | Statements | Coverage | Notes |
|--------|------------|----------|-------|
| `gaia.database.mixin` | 82 | **100%** | Excellent - full CRUD, transactions |
| `gaia.testing.assertions` | 67 | **85%** | Good test utilities |
| `gaia.testing.mocks` | 119 | **83%** | MockLLMProvider, MockVLMClient |
| `gaia.utils.file_watcher` | 208 | **78%** | File watching, hashing |
| `gaia.logger` | 84 | **73%** | Logging utilities |
| `gaia.utils.parsing` | 70 | **66%** | JSON extraction |
| `gaia.llm.lemonade_manager` | 123 | **61%** | Context messages |
| `gaia.database.testing` | 16 | **50%** | Test fixtures |

### Modules WITH Partial Coverage (10-50%)

| Module | Statements | Coverage | Notes |
|--------|------------|----------|-------|
| `gaia.agents.emr.cli` | 636 | **44%** | CLI tested, not watch/dashboard |
| `gaia.version` | 42 | **36%** | Version utilities |
| `gaia.agents.emr.agent` | 595 | **32%** | Init/parsing only |
| `gaia.testing.fixtures` | 104 | **28%** | Temp dir/file fixtures |
| `gaia.llm.vlm_client` | 131 | **21%** | Only MIME detection |
| `gaia.chat.sdk` | 477 | **17%** | Minimal coverage |
| `gaia.apps.llm.app` | 71 | **17%** | Basic app tests |
| `gaia.llm.llm_client` | 307 | **15%** | Only URL normalization |
| `gaia.eval.claude` | 190 | **15%** | Evaluation framework |
| `gaia.llm.lemonade_client` | 1,110 | **12%** | Backend client |

### CRITICAL Modules WITH 0% Coverage

| Module | Statements | Priority | Risk |
|--------|------------|----------|------|
| `gaia.cli` | 2,520 | **CRITICAL** | Main CLI entry point |
| `gaia.rag.sdk` | 994 | **CRITICAL** | Core RAG feature |
| `gaia.agents.base.agent` | 1,117 | **CRITICAL** | Core framework |
| `gaia.agents.code.tools.web_dev_tools` | 551 | HIGH | Code agent tools |
| `gaia.agents.chat.agent` | 421 | HIGH | User-facing agent |
| `gaia.agents.code.agent` | 406 | HIGH | User-facing agent |
| `gaia.agents.jira.agent` | 239 | HIGH | User-facing agent |
| `gaia.agents.docker.agent` | 188 | HIGH | Infrastructure |
| `gaia.agents.routing.agent` | 193 | HIGH | Routing logic |
| `gaia.api.openai_server` | 195 | MEDIUM | OpenAI compat |
| `gaia.api.app` | 129 | MEDIUM | API layer |
| `gaia.security` | 85 | MEDIUM | Security utils |

---

## 3. Test Classification Issues

### Tests Incorrectly Classified as Integration

These tests in `tests/` and `tests/mcp/` are actually unit tests:

| File | Lines | Issue |
|------|-------|-------|
| `test_code_agent.py` | 51-100 | Tests init/prompts, no I/O |
| `test_chat_agent.py` | 50-54, 84-90 | Tests init/search keys only |
| `test_mcp/test_agent_mcp_server.py` | 203-455 | Abstract class validation |
| `test_checklist_orchestration.py` | 57-80 | Template catalog checks |
| `test_external_tools.py` | 33-88 | Fully mocked tests |

**Recommendation:** Move to `tests/unit/` with proper isolation.

### Missing Integration Test Markers

Many integration tests lack proper `@pytest.mark.integration`:

```python
# Currently unmarked but requires Lemonade server
def test_chat_completion_with_llm(self):
    response = client.post("/v1/chat/completions", ...)
```

---

## 4. Agent-Related Tests for Migration

The following **17 test files** should be migrated to `amd/gaia-agents`:

### Root Tests

| File | Agent(s) | Lines |
|------|----------|-------|
| `test_chat_agent.py` | ChatAgent | 27K |
| `test_code_agent.py` | CodeAgent | 40K |
| `test_code_agent_mixins.py` | CodeAgent mixins | 15K |
| `test_jira.py` | JiraAgent | 129K |
| `test_sdk.py` | All agent base classes | 56K |
| `test_external_tools.py` | ExternalToolsMixin | 11K |
| `test_checklist_orchestration.py` | Code orchestration | 61K |
| `verify_path_validator.py` | Chat/Code/Docker agents | - |
| `verify_shell_security.py` | ChatAgent security | - |

### Integration Tests

| File | Agent(s) |
|------|----------|
| `integration/test_database_agent.py` | DatabaseAgent |
| `integration/test_database_mixin_integration.py` | Agent + DatabaseMixin |

### MCP Tests

| File | Agent(s) |
|------|----------|
| `mcp/test_agent_mcp_server.py` | MCPAgent, DockerAgent |

### Unit Tests

| File | Agent(s) |
|------|----------|
| `unit/test_emr_agent.py` | MedicalIntakeAgent |
| `unit/test_emr_cli.py` | EMR CLI commands |

### Embedded Source Tests

| File | Agent(s) |
|------|----------|
| `src/gaia/agents/blender/tests/test_agent.py` | BlenderAgent |
| `src/gaia/agents/blender/tests/test_agent_simple.py` | BlenderAgentSimple |
| `src/gaia/agents/blender/tests/test_mcp_client.py` | Blender MCP client |

---

## 5. Anti-Patterns Identified (VERIFIED)

### 5.1 Subprocess Testing in Unit Tests

```python
# tests/unit/test_llm.py:20-46 (VERIFIED)
def _run_normalization_test(self, input_url, expected_url):
    """Run a base_url normalization test in a subprocess to avoid bytecode cache issues."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, "src")
from gaia.llm.llm_client import LLMClient
...
"""],
        capture_output=True, text=True, timeout=30,
    )
```

**Problem:** Spawns subprocess for unit tests, defeating isolation.
**Fix:** Use proper mocking of LLMClient. The "bytecode cache" concern is not valid.

### 5.2 Global State Pollution (13 occurrences found)

```python
# VERIFIED locations of manual _TOOL_REGISTRY.clear():
# tests/test_code_agent.py:47, 620
# tests/test_code_agent_mixins.py:43, 78, 156, 197, 218, 267, 288, 345, 374
# tests/test_external_tools.py:266
# tests/test_typescript_tools.py:29
```

**Problem:** `_TOOL_REGISTRY` is a global singleton shared between tests.
**Fix:** Create pytest fixture that auto-clears registry.

### 5.3 Hardcoded Ports (25+ occurrences found)

```python
# VERIFIED locations (sample):
# tests/conftest.py:59, 95         - localhost:8000, localhost:8080
# tests/mcp/test_mcp_jira.py:22    - localhost:8765
# tests/mcp/test_mcp_simple.py:24  - localhost:8765
# tests/unit/test_llm.py:52,57,62  - localhost:8000
# tests/test_chat_sdk.py:42        - localhost:8000
# tests/test_rag_integration.py:17 - localhost:8000
```

**Problem:** Cannot run tests in parallel (port conflicts).
**Fix:** Use dynamic port allocation with `pytest-free-port` or socket binding to port 0.

### 5.4 Fixed Timeouts Without Backoff

```python
# tests/mcp/test_agent_mcp_server.py:115-130
while time.time() - start_time < timeout:
    time.sleep(2)  # Fixed delay
```

**Problem:** Flaky under load or slow CI.
**Fix:** Implement exponential backoff.

### 5.5 Mixed Test Frameworks

```python
# Some files use unittest.TestCase
class TestCodeAgent(unittest.TestCase):
    def setUp(self): ...

# Others use pytest
class TestFileWatcher:  # No inheritance
    def test_something(self): ...
```

**Problem:** Inconsistent patterns, fixture incompatibility.
**Fix:** Standardize on pytest.

---

## 6. Fixture Issues

### Current Fixtures (conftest.py)

| Fixture | Scope | Issues |
|---------|-------|--------|
| `lemonade_available` | session | Hardcoded port |
| `require_lemonade` | function | OK |
| `api_server` | function | Hardcoded port, manual cleanup |
| `api_client` | function | OK |

### Missing Fixtures

| Fixture | Purpose | Priority |
|---------|---------|----------|
| `tool_registry` | Auto-clear global registry | HIGH |
| `temp_workspace` | Isolated file workspace | HIGH |
| `mock_llm` | Standardized LLM mock | HIGH |
| `dynamic_port` | Parallel test support | MEDIUM |
| `mock_docker` | Docker operation mock | MEDIUM |

---

## 7. Recommendations

### Phase 1: Immediate Cleanup (1-2 days)

1. **Create proper test markers**
   ```toml
   # pyproject.toml
   markers = [
       "slow: marks tests as slow (> 5 seconds)",
       "integration: requires external services",
       "requires_docker: requires Docker daemon",
       "requires_lemonade: requires Lemonade server",
       "agent: agent-related test (future migration)",
   ]
   ```

2. **Add `tool_registry` fixture**
   ```python
   # conftest.py
   @pytest.fixture(autouse=True)
   def clean_tool_registry():
       from gaia.agents.base.tools import _TOOL_REGISTRY
       yield
       _TOOL_REGISTRY.clear()
   ```

3. **Mark agent tests for migration**
   ```python
   @pytest.mark.agent  # Tag for future migration
   class TestChatAgent:
       ...
   ```

### Phase 2: Reorganization (3-5 days)

1. **Move misclassified tests**
   ```
   # Unit tests currently in root
   tests/test_code_agent.py:51-100 → tests/unit/test_code_agent_init.py
   tests/test_chat_agent.py:50-90 → tests/unit/test_chat_agent_init.py
   tests/mcp/test_agent_mcp_server.py:203-455 → tests/unit/test_mcp_agent.py
   ```

2. **Standardize on pytest**
   - Remove `unittest.TestCase` inheritance
   - Convert `setUp`/`tearDown` to fixtures
   - Use `pytest.raises` instead of `self.assertRaises`

3. **Add missing `conftest.py` files**
   ```
   tests/unit/conftest.py       # Unit test fixtures
   tests/integration/conftest.py # Integration fixtures
   tests/mcp/conftest.py        # MCP test fixtures
   ```

### Phase 3: Coverage Expansion (1-2 weeks)

1. **Priority unit tests to add**
   ```
   tests/unit/test_agent_base.py       # Base Agent class
   tests/unit/test_agent_tools.py      # Tool registration/execution
   tests/unit/test_chat_sdk.py         # Chat SDK methods
   tests/unit/test_rag_sdk.py          # RAG SDK methods
   tests/unit/test_mcp_client.py       # MCP client logic
   ```

2. **Remove subprocess anti-pattern**
   - Refactor `tests/unit/test_llm.py` to use mocking
   - Create `MockLLMClient` fixture

### Phase 4: Agent Migration Prep

1. **Create agent test manifest**
   ```yaml
   # tests/agent_tests.yaml
   migration_target: amd/gaia-agents
   files:
     - tests/test_chat_agent.py
     - tests/test_code_agent.py
     - tests/test_jira.py
     # ... etc
   ```

2. **Ensure test portability**
   - Extract shared fixtures to importable module
   - Document required test dependencies
   - Create mock implementations for non-agent code

---

## 8. Target Test Structure

Tests should be organized by **test type** (unit/integration), not by technology (mcp/electron). This ensures consistent patterns and makes it clear what dependencies each test requires.

```
tests/
├── conftest.py                    # Global fixtures
├── unit/                          # Pure unit tests (no I/O, mocked deps)
│   ├── conftest.py
│   ├── llm/
│   │   ├── test_llm_client.py
│   │   └── test_lemonade_manager.py
│   ├── rag/
│   │   └── test_rag_sdk.py
│   ├── chat/
│   │   └── test_chat_sdk.py
│   ├── mcp/                       # MCP protocol parsing, validation
│   │   ├── test_protocol.py
│   │   └── test_message_validation.py
│   ├── utils/
│   │   ├── test_file_watcher.py
│   │   └── test_parsing.py
│   ├── database/
│   │   └── test_mixin.py
│   └── audio/
│       ├── test_asr.py
│       └── test_tts.py
├── integration/                   # Tests requiring external services
│   ├── conftest.py
│   ├── llm/
│   │   └── test_lemonade_client.py
│   ├── api/
│   │   └── test_api_server.py
│   ├── rag/
│   │   └── test_rag_pipeline.py
│   ├── mcp/                       # MCP with real bridge/servers
│   │   ├── test_mcp_bridge.py
│   │   ├── test_mcp_jira.py
│   │   └── test_mcp_http.py
│   └── vlm/
│       └── test_vlm_pipeline.py
├── e2e/                           # End-to-end workflows
│   └── ...
├── js/                            # JavaScript tests (separate toolchain)
│   ├── package.json               # Jest/Vitest config
│   ├── unit/
│   │   └── test_ipc_handler.js
│   └── integration/
│       ├── test_electron_app.js
│       └── test_jira_app.js
└── _migrating/                    # TEMPORARY - pending move to gaia-agents
    ├── README.md                  # Migration notes
    └── ...
```

### Why This Structure?

| Principle | Rationale |
|-----------|-----------|
| **Organize by test type, not technology** | MCP tests can be unit (protocol parsing) or integration (real servers) |
| **Subdirectories mirror source** | `tests/unit/llm/` tests `src/gaia/llm/` |
| **Separate JS tests** | Different toolchain (Jest/Vitest), different conftest |
| **Clear dependencies** | `unit/` = no I/O; `integration/` = services required |

---

## 9. CI/CD Recommendations

### Test Stage Configuration

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit/ -v --cov --cov-report=xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      lemonade:
        image: amd/lemonade:latest
        ports:
          - 8000:8000
    steps:
      - run: pytest tests/integration/ -v -m integration

  js-tests:
    runs-on: ubuntu-latest
    steps:
      - run: cd tests/js && npm ci && npm test
```

Note: MCP tests are distributed across `unit/mcp/` and `integration/mcp/` based on whether they need real servers.

### Parallel Execution Support

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--tb=short --strict-markers -n auto"  # pytest-xdist
```

---

## 10. Summary Checklist

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Add test markers | HIGH | 1h | Pending |
| Add tool_registry fixture | HIGH | 30m | Pending |
| Move misclassified unit tests | HIGH | 2h | Pending |
| Mark agent tests for migration | HIGH | 1h | Pending |
| Standardize on pytest | MEDIUM | 4h | Pending |
| Add conftest.py per directory | MEDIUM | 2h | Pending |
| Add unit tests for Agent base | HIGH | 8h | Pending |
| Remove subprocess anti-pattern | MEDIUM | 2h | Pending |
| Implement dynamic ports | MEDIUM | 4h | Pending |
| Implement exponential backoff | LOW | 2h | Pending |
| Create agent migration manifest | LOW | 1h | Pending |

---

## Appendix A: Recommended Test Structure for `amd/gaia-agents`

The `gaia-agents` repository should be set up with proper testing patterns from the start. This structure assumes agents will depend on `gaia` as a library.

### Directory Structure

```
gaia-agents/
├── src/
│   └── gaia_agents/
│       ├── __init__.py
│       ├── chat/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── tools/
│       ├── code/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── orchestration/
│       │   └── tools/
│       ├── jira/
│       │   ├── __init__.py
│       │   └── agent.py
│       ├── blender/
│       │   ├── __init__.py
│       │   └── agent.py
│       ├── docker/
│       │   ├── __init__.py
│       │   └── agent.py
│       ├── emr/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── cli.py
│       └── routing/
│           ├── __init__.py
│           └── agent.py
├── tests/
│   ├── conftest.py                # Shared fixtures
│   ├── unit/                      # Pure unit tests (mocked dependencies)
│   │   ├── conftest.py
│   │   ├── chat/
│   │   │   ├── test_agent.py
│   │   │   └── test_tools.py
│   │   ├── code/
│   │   │   ├── test_agent.py
│   │   │   ├── test_orchestration.py
│   │   │   └── test_tools.py
│   │   ├── jira/
│   │   │   └── test_agent.py
│   │   ├── blender/
│   │   │   └── test_agent.py
│   │   ├── docker/
│   │   │   └── test_agent.py
│   │   ├── emr/
│   │   │   ├── test_agent.py
│   │   │   └── test_cli.py
│   │   └── routing/
│   │       └── test_agent.py
│   ├── integration/               # Tests requiring gaia services
│   │   ├── conftest.py
│   │   ├── test_chat_with_rag.py
│   │   ├── test_code_with_llm.py
│   │   └── test_jira_with_api.py
│   ├── contract/                  # Contract tests against gaia SDK
│   │   ├── test_base_agent_contract.py
│   │   └── test_tool_registry_contract.py
│   └── e2e/                       # End-to-end agent workflows
│       ├── test_chat_conversation.py
│       └── test_code_generation.py
├── pyproject.toml
└── README.md
```

### Root conftest.py

```python
# tests/conftest.py
"""
Shared fixtures for gaia-agents test suite.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


# =============================================================================
# TOOL REGISTRY ISOLATION (CRITICAL)
# =============================================================================

@pytest.fixture(autouse=True)
def isolate_tool_registry():
    """
    Automatically isolate tool registry for every test.
    Prevents global state pollution between tests.
    """
    from gaia.agents.base.tools import _TOOL_REGISTRY
    original_state = _TOOL_REGISTRY.copy()
    yield
    _TOOL_REGISTRY.clear()
    _TOOL_REGISTRY.update(original_state)


# =============================================================================
# LLM MOCKING
# =============================================================================

@pytest.fixture
def mock_llm_client():
    """
    Mock LLM client for unit tests.
    Returns predictable responses without network calls.
    """
    client = MagicMock()
    client.chat.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mock response"))]
    )
    client.chat_stream = AsyncMock(return_value=iter([
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Mock "))])
    ]))
    return client


@pytest.fixture
def mock_chat_sdk(mock_llm_client):
    """
    Mock ChatSDK for agent testing.
    """
    from unittest.mock import patch
    with patch("gaia.chat.sdk.ChatSDK") as MockChatSDK:
        instance = MockChatSDK.return_value
        instance.chat.return_value = "Mock agent response"
        instance.chat_stream = AsyncMock()
        yield instance


# =============================================================================
# AGENT FIXTURES
# =============================================================================

@pytest.fixture
def base_agent_config():
    """Base configuration for agent instantiation."""
    return {
        "model": "test-model",
        "max_tokens": 100,
        "temperature": 0.0,
    }


@pytest.fixture
def temp_workspace(tmp_path):
    """
    Isolated temporary workspace for file operations.
    Each test gets a fresh directory.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


# =============================================================================
# SERVICE AVAILABILITY CHECKS
# =============================================================================

@pytest.fixture(scope="session")
def gaia_sdk_available():
    """Check if gaia SDK is importable."""
    try:
        import gaia
        return True
    except ImportError:
        return False


@pytest.fixture
def require_gaia_sdk(gaia_sdk_available):
    """Skip test if gaia SDK not available."""
    if not gaia_sdk_available:
        pytest.skip("gaia SDK not installed")
```

### Unit Test conftest.py

```python
# tests/unit/conftest.py
"""
Unit test fixtures - no external dependencies.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_file_system(temp_workspace):
    """
    Mock file system operations.
    Redirects all file I/O to temp workspace.
    """
    with patch("builtins.open", create=True) as mock_open:
        yield mock_open


@pytest.fixture
def mock_subprocess():
    """
    Mock subprocess calls for shell tool tests.
    """
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="success",
            stderr=""
        )
        yield mock_run
```

### Integration Test conftest.py

```python
# tests/integration/conftest.py
"""
Integration test fixtures - require gaia services.
"""
import pytest
import requests


@pytest.fixture(scope="session")
def lemonade_available():
    """Check if Lemonade server is running."""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


@pytest.fixture
def require_lemonade(lemonade_available):
    """Skip integration test if Lemonade not available."""
    if not lemonade_available:
        pytest.skip("Lemonade server not available")


@pytest.fixture
def live_llm_client(require_lemonade):
    """
    Real LLM client for integration tests.
    Only created when Lemonade is available.
    """
    from gaia.llm import LLMClient
    return LLMClient(base_url="http://localhost:8000")
```

### pyproject.toml Configuration

```toml
[project]
name = "gaia-agents"
version = "0.1.0"
dependencies = [
    "gaia>=0.1.0",  # Core SDK dependency
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-xdist>=3.5.0",  # Parallel execution
    "pytest-timeout>=2.2.0",
    "responses>=0.25.0",    # HTTP mocking
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--tb=short --strict-markers -v"
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (> 5 seconds)",
    "integration: requires external services (Lemonade, Docker)",
    "e2e: end-to-end tests requiring full stack",
    "contract: contract tests against gaia SDK",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src/gaia_agents"]
branch = true
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
fail_under = 80  # Enforce 80% coverage minimum
```

### Example Unit Test Pattern

```python
# tests/unit/chat/test_agent.py
"""
Unit tests for ChatAgent - no external dependencies.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestChatAgentInit:
    """Test ChatAgent initialization."""

    def test_init_with_defaults(self, mock_chat_sdk):
        """Agent initializes with default configuration."""
        from gaia_agents.chat import ChatAgent

        agent = ChatAgent()

        assert agent.model is not None
        assert agent.max_tokens > 0

    def test_init_with_custom_config(self, mock_chat_sdk, base_agent_config):
        """Agent accepts custom configuration."""
        from gaia_agents.chat import ChatAgent

        agent = ChatAgent(**base_agent_config)

        assert agent.model == "test-model"
        assert agent.max_tokens == 100


class TestChatAgentTools:
    """Test ChatAgent tool registration."""

    def test_default_tools_registered(self, mock_chat_sdk):
        """Default tools are registered on init."""
        from gaia_agents.chat import ChatAgent

        agent = ChatAgent()

        assert "read_file" in agent.tools
        assert "search_files" in agent.tools

    def test_custom_tool_registration(self, mock_chat_sdk):
        """Custom tools can be registered."""
        from gaia_agents.chat import ChatAgent

        agent = ChatAgent()

        @agent.tool
        def custom_tool(x: int) -> int:
            return x * 2

        assert "custom_tool" in agent.tools


class TestChatAgentChat:
    """Test ChatAgent chat functionality."""

    def test_chat_returns_response(self, mock_chat_sdk):
        """Chat method returns LLM response."""
        from gaia_agents.chat import ChatAgent

        agent = ChatAgent()
        response = agent.chat("Hello")

        assert response == "Mock agent response"
        mock_chat_sdk.chat.assert_called_once()

    def test_chat_with_context(self, mock_chat_sdk, temp_workspace):
        """Chat uses provided context."""
        from gaia_agents.chat import ChatAgent

        agent = ChatAgent(workspace=temp_workspace)
        agent.chat("Summarize the files")

        # Verify context was included in chat call
        call_args = mock_chat_sdk.chat.call_args
        assert call_args is not None
```

### Example Integration Test Pattern

```python
# tests/integration/test_chat_with_rag.py
"""
Integration tests for ChatAgent with RAG.
Requires Lemonade server running.
"""
import pytest


@pytest.mark.integration
class TestChatAgentRAGIntegration:
    """Test ChatAgent with real RAG functionality."""

    def test_chat_with_indexed_documents(
        self, require_lemonade, live_llm_client, temp_workspace
    ):
        """Agent can answer questions from indexed documents."""
        from gaia_agents.chat import ChatAgent
        from gaia.rag import RAGSDK

        # Setup: Create and index a test document
        doc_path = temp_workspace / "test.txt"
        doc_path.write_text("The answer is 42.")

        rag = RAGSDK()
        rag.index_document(doc_path)

        # Test: Agent answers from indexed content
        agent = ChatAgent(rag=rag, llm_client=live_llm_client)
        response = agent.chat("What is the answer?")

        assert "42" in response
```

### CI/CD Configuration for gaia-agents

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"
      - name: Run unit tests with coverage
        run: |
          pytest tests/unit/ -v --cov --cov-report=xml --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  contract-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"
      - name: Run contract tests
        run: pytest tests/contract/ -v

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      lemonade:
        image: amd/lemonade:latest
        ports:
          - 8000:8000
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"
      - name: Wait for Lemonade
        run: |
          timeout 60 bash -c 'until curl -s http://localhost:8000/api/v1/health; do sleep 2; done'
      - name: Run integration tests
        run: pytest tests/integration/ -v -m integration
```

### Key Principles for gaia-agents Testing

1. **Isolation First**: Every test should be independent. The `isolate_tool_registry` fixture is `autouse=True`.

2. **Mock by Default**: Unit tests mock all external dependencies (LLM, file system, network).

3. **Contract Tests**: Verify compatibility with the gaia SDK API to catch breaking changes early.

4. **Coverage Enforcement**: `fail_under = 80` in pyproject.toml prevents coverage regression.

5. **Parallel Execution**: Use `pytest-xdist` with dynamic port allocation for CI speed.

6. **Clear Test Categories**:
   - `unit/` - Fast, isolated, no I/O
   - `integration/` - Requires services
   - `contract/` - SDK compatibility
   - `e2e/` - Full workflow tests

---

## Appendix B: Files to Migrate to amd/gaia-agents

```
# Root level
tests/test_chat_agent.py
tests/test_code_agent.py
tests/test_code_agent_mixins.py
tests/test_jira.py
tests/test_sdk.py (agent portions)
tests/test_external_tools.py
tests/test_checklist_orchestration.py
tests/verify_path_validator.py
tests/verify_shell_security.py

# Integration
tests/integration/test_database_agent.py
tests/integration/test_database_mixin_integration.py

# MCP
tests/mcp/test_agent_mcp_server.py

# Unit
tests/unit/test_emr_agent.py
tests/unit/test_emr_cli.py

# Embedded
src/gaia/agents/blender/tests/test_agent.py
src/gaia/agents/blender/tests/test_agent_simple.py
src/gaia/agents/blender/tests/test_mcp_client.py
src/gaia/agents/blender/tests/conftest.py
```

---

## Appendix B: Non-Agent Tests to Keep

```
# Unit tests
tests/unit/test_llm.py
tests/unit/test_file_watcher.py
tests/unit/test_testing_utilities.py
tests/unit/test_asr.py
tests/unit/test_tts.py
tests/unit/test_errors.py
tests/unit/test_database_mixin.py

# Integration tests
tests/test_api.py
tests/test_lemonade_client.py
tests/test_lemonade_embeddings.py
tests/test_rag.py
tests/test_rag_integration.py
tests/test_chat_sdk.py
tests/test_summarizer.py
tests/test_vlm_integration.py
tests/test_typescript_tools.py

# MCP tests (non-agent)
tests/mcp/test_mcp_http_validation.py
tests/mcp/test_mcp_simple.py
tests/mcp/test_mcp_integration.py
tests/mcp/test_mcp_jira.py (partial)

# Electron tests
tests/electron/*
```
