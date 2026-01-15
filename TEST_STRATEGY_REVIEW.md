# GAIA Test Strategy Review

> **Date:** 2026-01-15
> **Repository:** amd/gaia (gaia-pirate)
> **Reviewer:** Claude Code Analysis

---

## Executive Summary

The GAIA test suite has **solid foundations** but suffers from **organizational inconsistencies**, **significant coverage gaps**, and **mixed test classifications**. This review identifies issues and provides actionable recommendations for cleanup, consolidation, and alignment with proper testing patterns.

**Key Findings:**
- **176 source modules** with only **~12 having proper unit tests** (~7% coverage)
- **~20% of integration tests should be unit tests**
- **17 agent-related test files** to be migrated to `amd/gaia-agents`
- Inconsistent frameworks (unittest.TestCase vs pytest)
- Hardcoded ports prevent parallel test execution
- Global state pollution between tests

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

### Test Statistics

| Metric | Value |
|--------|-------|
| Total Python test files | 36 |
| Total test functions | ~765+ |
| Total test classes | ~111+ |
| Lines of test code | ~21,600 |
| Source modules | 176 |
| Modules with unit tests | ~12 |
| **Estimated unit coverage** | **~7%** |

---

## 2. Coverage Analysis

### Modules WITH Unit Tests

| Module | Coverage | Quality |
|--------|----------|---------|
| `gaia.utils.file_watcher` | Good | 24 test methods |
| `gaia.database.mixin` | Excellent | Full CRUD, transactions |
| `gaia.agents.base.errors` | Good | Error formatting |
| `gaia.audio.whisper_asr` | Fair | Hardware-dependent |
| `gaia.audio.kokoro_tts` | Fair | Hardware-dependent |
| `gaia.llm.llm_client` | Partial | Only URL normalization |
| `gaia.testing` | Good | Test utilities |
| `gaia.agents.emr` | Partial | Init/parsing only |

### CRITICAL Modules WITHOUT Unit Tests

| Module | Priority | Risk |
|--------|----------|------|
| `gaia.agents.base.agent` (6.4K LOC) | **CRITICAL** | Core framework |
| `gaia.agents.chat.agent` | **CRITICAL** | User-facing |
| `gaia.agents.code.agent` | **CRITICAL** | User-facing |
| `gaia.agents.jira.agent` | HIGH | User-facing |
| `gaia.agents.docker.agent` | HIGH | Infrastructure |
| `gaia.mcp.*` (all modules) | HIGH | Integration layer |
| `gaia.rag.sdk` | HIGH | Core feature |
| `gaia.chat.sdk` | HIGH | Core SDK |
| `gaia.api.app` | MEDIUM | API layer |
| `gaia.llm.lemonade_client` | MEDIUM | Backend client |

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

## 5. Anti-Patterns Identified

### 5.1 Subprocess Testing in Unit Tests

```python
# tests/unit/test_llm.py:22-46
result = subprocess.run([sys.executable, "-c", f"""..."""])
```

**Problem:** Spawns subprocess for unit tests, defeating isolation.
**Fix:** Use proper mocking of LLMClient.

### 5.2 Global State Pollution

```python
# tests/test_code_agent.py:46-47
def tearDown(self):
    _TOOL_REGISTRY.clear()  # Manual cleanup required
```

**Problem:** `_TOOL_REGISTRY` is a global singleton shared between tests.
**Fix:** Create pytest fixture that auto-clears registry.

### 5.3 Hardcoded Ports

```python
# tests/conftest.py:95, tests/mcp/*.py
api_url = "http://localhost:8080"
lemonade_url = "http://localhost:8000"
mcp_url = "http://localhost:8765"
```

**Problem:** Cannot run tests in parallel.
**Fix:** Use dynamic port allocation with `pytest-free-port`.

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
