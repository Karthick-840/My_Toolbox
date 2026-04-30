# GitHub Gatekeeper Setup For Branches

This guide ensures feature branches and main are protected by CI checks before merge.

## 1. Workflows included

- CI Gatekeeper: [.github/workflows/ci.yml](../.github/workflows/ci.yml)
- Package Quality: [.github/workflows/package.yml](../.github/workflows/package.yml)
- Security Audit: [.github/workflows/security.yml](../.github/workflows/security.yml)
- Publish Package: [.github/workflows/publish.yml](../.github/workflows/publish.yml)

## 2. What runs where

- Feature branches and main:
  - CI Gatekeeper runs on push and PR.
  - Package Quality runs on PR and main push.
  - Security Audit runs on PR, main push, and weekly schedule.
- Release publish:
  - Publish Package runs on GitHub release published.

## 3. Enable branch protection in GitHub UI

For main and any long-lived integration branch (for example develop):

1. Go to repository Settings > Branches > Add branch protection rule.
2. Rule pattern: main.
3. Enable "Require a pull request before merging".
4. Enable "Require status checks to pass before merging".
5. Select these required checks:
   - CI Gatekeeper / lint-and-test
   - Package Quality / build-and-verify
   - Security Audit / dependency-audit
6. Optionally enable:
   - Require branches to be up to date before merging
   - Require conversation resolution before merging
   - Include administrators

For feature branches, create a second protection rule if needed:

1. Add rule for feature/* (or feat/*, bugfix/*).
2. Require status checks if you want strict gatekeeping before promoting to main.

## 4. Recommended branch flow

1. Create feature branch from main.
2. Push commits to feature branch.
3. CI Gatekeeper runs immediately.
4. Open PR to main.
5. All required checks must pass.
6. Merge only after approvals and green checks.

## 5. Release flow

1. Merge to main.
2. Create a GitHub release.
3. Publish Package workflow builds and publishes to PyPI.

## 6. PyPI publish prerequisites

Use trusted publishing:

1. In PyPI project settings, add GitHub trusted publisher for this repo.
2. Environment name should match workflow: pypi.
3. Keep id-token permission enabled in publish workflow.
