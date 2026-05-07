# Automated Bootstrap Guide

## One-Click Automation: Close Laptop, Come Back to Completed Code

The bootstrap automation is fully hands-off. You can close your laptop and come back to:
- ✅ All code generated from the plans
- ✅ All tests run and passing
- ✅ PR created for review (or auto-merged if configured)
- ✅ Full audit trail in GitHub

## Option 1: Manual Trigger (Recommended First Time)

### Step 1: Go to GitHub Actions
```
https://github.com/Karthick-840/My_Toolbox/actions/workflows/auto-bootstrap-agentic-langchain.yml
```

### Step 2: Click "Run workflow"
- **Phase**: Select `phase-0-1-contracts`
- **Auto-merge**: Leave unchecked first time (review code before merging)
- Click **Run workflow**

### Step 3: Come Back Later
- Workflow runs automatically (~10 minutes)
- Check email for completion notification
- PR is created at: `Settings > Pull Requests > Open`
- Review generated code at the PR
- Merge if looks good

## Option 2: Scheduled Automation (Hands-Off)

Every Monday at 2 AM UTC, the workflow automatically:
1. Generates code for the next phase
2. Runs all tests
3. Creates a PR
4. Posts status comment

You just wake up to a ready-to-review PR.

**To customize the schedule:**
Edit `.github/workflows/auto-bootstrap-agentic-langchain.yml`:
```yaml
schedule:
  - cron: '0 2 * * 1'  # <- Change this (crontab format)
```

## Option 3: Fully Autonomous (Auto-Merge)

If you trust the automation and want zero waiting:

### First Time Setup
1. Manual trigger with **Auto-merge = true**
2. Watch it run
3. Confirm it merged clean

### Then for Future Phases
Just push a commit that triggers the schedule or manual run — code merges automatically if tests pass.

## What Gets Generated (Phase 0-1)

When you trigger **phase-0-1-contracts**:

```
agentic_toolbox/
  __init__.py                  # Package exports
  contracts/
    __init__.py
    tool_contracts.py          # ToolSpec, ToolTag, etc.
  registry/
    __init__.py
    tool_registry.py           # Central tool registry
  executor/
    __init__.py
    tool_executor.py           # Policy enforcement
  tests/
    test_registry.py           # Unit tests
```

All code extracted from: `docs/Phase_0_1_Bootstrap_Code.md`

## Local Testing (Before Pushing)

Test the generator locally first:

```bash
# Dry-run (don't actually create files)
python scripts/bootstrap_generator.py --phase phase-0-1-contracts --dry-run

# Create files for real
python scripts/bootstrap_generator.py --phase phase-0-1-contracts

# Check what was created
cat BOOTSTRAP_MANIFEST.txt
```

Then validate:
```bash
pytest agentic_toolbox/tests/ -v
ruff check agentic_toolbox/
mypy agentic_toolbox/contracts/ --ignore-missing-imports
```

## What If It Fails?

Check the GitHub Actions logs:

1. Click the workflow run
2. Open the "Generate Code from Plan" job
3. Look for error messages
4. Common issues:
   - **SyntaxError in generated code**: Plan markdown has bad Python (fix in `docs/Phase_0_1_Bootstrap_Code.md`)
   - **File already exists**: Files from a previous run exist (safe to retry)
   - **Missing dependencies**: Check `pip install` logs

## Workflow Steps (Transparent)

```
1. bootstrap-code
   ├─ Extract code from markdown
   ├─ Create Python files
   └─ Commit changes to bootstrap/phase-0-1 branch

2. validate-generated (runs in parallel)
   ├─ Lint code (ruff)
   ├─ Type check (mypy)
   ├─ Run unit tests (pytest)
   └─ Upload test report

3. create-pr (if auto_merge=false)
   └─ Create PR to main with details

4. auto-merge (if auto_merge=true)
   ├─ Merge bootstrap/phase-0-1 → main
   └─ Delete bootstrap branch

5. notify
   └─ Post status comment with details
```

## How to Enable GitHub Token for Auto-Commit

By default, the workflow uses `${{ secrets.GITHUB_TOKEN }}` which GitHub provides automatically. **Nothing to set up.**

If you want explicit control, that's already baked in.

## Template for Creating More Phases

When you're ready for Phase 2, 3, 4:

1. Create markdown docs:
   - `docs/Phase_2_Registry_Executor.md`
   - `docs/Phase_3_MCP_Server.md`
   - etc.

2. Add code blocks following the pattern:
   ```markdown
   ## File 1: agentic_toolbox/...
   ```python
   ...code...
   ```
   ```

3. Update `scripts/bootstrap_generator.py`:
   ```python
   def bootstrap_phase_2(self) -> bool:
       plan_file = self.repo_root / "docs" / "Phase_2_...md"
       # ... same logic
   ```

4. Add phase to workflow inputs:
   ```yaml
   type: choice
   options:
     - phase-0-1-contracts
     - phase-2-registry-executor
   ```

5. Call in workflow:
   ```bash
   python scripts/bootstrap_generator.py --phase ${{ github.event.inputs.phase }}
   ```

## TL;DR: The Fastest Path

**Right now:**
```bash
git add .github/workflows/auto-bootstrap-agentic-langchain.yml scripts/bootstrap_generator.py
git commit -m "add: automated bootstrap workflow"
git push
```

**Tomorrow:**
1. Go to: Actions > `auto-bootstrap-agentic-langchain`
2. Click: "Run workflow"
3. Select: `phase-0-1-contracts`, uncheck auto-merge
4. Close laptop

**When you get back:**
- Email notification saying workflow passed
- PR ready for review
- Click Merge when satisfied

**Zero manual code creation needed.**
