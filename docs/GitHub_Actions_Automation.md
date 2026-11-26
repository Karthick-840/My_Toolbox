# GitHub Actions Automation for Agentic + LangChain Toolboxes

## Overview
The workflow (`.github/workflows/agentic-langchain-ci.yml`) automates **all CI/CD** for both toolboxes **without needing the agentic framework itself**.

## What Runs Automatically

### On Every PR to main/develop
1. **Lint** — ruff + mypy checks
2. **Unit Tests** — llm_toolbox (required), agentic (permissive), langchain (permissive)
3. **Security** — bandit + safety checks
4. **Contracts** — ToolSpec conformance (Phase 1+)
5. **Status Summary** — Posts comment on PR

### On Every Push to main
1. All PR checks
2. **Build Artifacts** — Wheels for llm_toolbox
3. **MCP Smoke** — Stub until Phase 3
4. **A2A Smoke** — Stub until Phase 4

## Requirements (No Framework Needed)

Check that your repo has:

### 1. Minimal pyproject.toml entries
```toml
[project]
name = "llm_toolbox"
version = "0.1.0"
dependencies = [...]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy", "pytest-cov"]
```

### 2. Tests directory structure
```
llm_toolbox/tests/
  test_*.py        # Required (workflow runs these)
agentic_toolbox/tests/
  test_*.py        # Optional (workflow continues if missing)
langchain_adapters/tests/
  test_*.py        # Optional (workflow continues if missing)
```

### 3. GitHub repo settings
Enable Actions in Settings > Actions > Allow all actions and reusable workflows.

## Phase-by-Phase Unlocking

### Phase 0 (Now)
```yaml
✓ Lint & type checks
✓ llm_toolbox unit tests
✓ Security scans
⚠ agentic_toolbox tests (no-op, continues on error)
⚠ langchain_adapters tests (no-op, continues on error)
```

### Phase 1 (Extract Contracts)
```yaml
✓ Add agentic_toolbox/contracts/tool_contracts.py
✓ Uncomment contract tests in test_contracts job
✗ Workflow now fails if tool specs invalid
```

### Phase 2 (Add Registry)
```yaml
✓ Add tests/test_registry.py to agentic_toolbox
✓ Workflow runs real agentic_toolbox unit tests
✗ Workflow now enforces agentic_toolbox tests passing
```

### Phase 3 (MCP MVP)
```yaml
✓ Implement protocols/mcp_server.py
✓ Update smoke-mcp job to start real server
✓ Workflow validates MCP list_tools endpoint
```

### Phase 4 (A2A MVP)
```yaml
✓ Implement protocols/a2a_server.py
✓ Update smoke-a2a job to start real server
✓ Workflow validates A2A task submission
```

## Configuration

### Environment Variables (GitHub Secrets)
If using cloud providers for tests, add to repo Settings > Secrets > Actions:

```
GOOGLE_API_KEY          (for Gemini tests)
GROQ_API_KEY            (for Groq tests)
DEEPSEEK_API_KEY        (optional deepseek tests)
```

Pass them in workflow:
```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

### Customize for Your Repo
Edit workflow path filters if toolboxes live elsewhere:
```yaml
paths:
  - 'path/to/agentic_toolbox/**'    # Update if needed
  - 'path/to/langchain_adapters/**'
  - 'path/to/llm_toolbox/**'
```

## Status Indicators

### PR Comment Example
```
## CI Status ✅
- **llm_toolbox**: Tests passed
- **agentic_toolbox**: Phase 0 ready (Phase 1+ pending)
- **langchain_adapters**: Phase 0 ready (Phase 1+ pending)

See details: [Workflow Run](https://github.com/...)
```

### Workflow Badge
Add to README.md:
```markdown
![CI/CD](https://github.com/Karthick-840/My_Toolbox/actions/workflows/agentic-langchain-ci.yml/badge.svg)
```

## Debugging Failed Runs

1. Click workflow run in Actions tab
2. Open job logs (e.g., "Test llm_toolbox")
3. Check for:
   - Missing imports (fix in __init__.py)
   - Test discovery (ensure tests/ exists)
   - Cache issues (Actions > Cache > Clear)

## Next Steps

1. **Now**: Push .github/workflows/agentic-langchain-ci.yml to repo
2. **Phase 1**: Create agentic_toolbox/contracts/tool_contracts.py with ToolSpec model
3. **Phase 2**: Add agentic_toolbox/tests/test_registry.py
4. **Phase 3**: Implement MCP server and wire smoke test
5. **Phase 4**: Implement A2A server and wire smoke test

## Cost Considerations

GitHub Actions free tier includes 2000 minutes/month on Ubuntu.

- Typical run: ~5 min (lint + tests)
- 10 PRs/day = ~50 min/day = ~25 hours/month ✓ Safe

If exceeding limits, consider:
- Run tests only on main merges (remove pull_request trigger)
- Use smaller matrix (single Python version instead of 3 versions)
- Cache dependencies aggressively

## Override Matrix (Optional Advanced)

Expand tests to multiple Python versions:
```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.11', '3.12']
```

Then use:
```yaml
- uses: actions/setup-python@v4
  with:
    python-version: ${{ matrix.python-version }}
```

## Rollback

If workflow breaks deployment:
1. Edit workflow to add `if: false` on build/smoke jobs
2. Push disable
3. Fix implementation
4. Remove `if: false` and retry

```yaml
build:
  if: false  # Disable entire job
  runs-on: ubuntu-latest
```
