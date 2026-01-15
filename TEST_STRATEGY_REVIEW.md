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

```
tests/
├── conftest.py                    # Global fixtures
├── unit/                          # Pure unit tests (no I/O)
│   ├── conftest.py
│   ├── test_llm_client.py
│   ├── test_chat_sdk.py
│   ├── test_rag_sdk.py
│   ├── test_mcp_protocol.py
│   ├── test_file_watcher.py
│   ├── test_database_mixin.py
│   ├── test_errors.py
│   ├── test_asr.py
│   └── test_tts.py
├── integration/                   # Service integration tests
│   ├── conftest.py
│   ├── test_api_server.py
│   ├── test_lemonade_client.py
│   ├── test_rag_pipeline.py
│   └── test_vlm_pipeline.py
├── mcp/                           # MCP protocol tests
│   ├── conftest.py
│   ├── test_mcp_http.py
│   ├── test_mcp_bridge.py
│   └── test_mcp_jira.py
├── electron/                      # JavaScript Electron tests
│   └── ...
└── agent/                         # TEMPORARY - pending migration
    ├── README.md                  # Migration notes
    ├── test_chat_agent.py
    ├── test_code_agent.py
    ├── test_jira_agent.py
    └── ...
```

---

## 9. CI/CD Recommendations

### Test Stage Configuration

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit/ -v --tb=short

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      lemonade:
        image: amd/lemonade:latest
    steps:
      - run: pytest tests/integration/ -m integration -v

  mcp-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - run: pytest tests/mcp/ -v --tb=short
```

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

## Appendix A: Files to Migrate to amd/gaia-agents

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
