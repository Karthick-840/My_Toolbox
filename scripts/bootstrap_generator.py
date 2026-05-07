#!/usr/bin/env python3
"""Auto-bootstrap code generator for Agentic + LangChain toolboxes.

This script reads the Phase plans from markdown and generates actual Python files.
Can be run manually or by GitHub Actions workflow.

Usage:
    python scripts/bootstrap_generator.py --phase phase-0-1-contracts
    python scripts/bootstrap_generator.py --phase phase-0-1-contracts --validate-only
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class BootstrapGenerator:
    """Extracts and generates code from markdown plans."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.repo_root = Path(__file__).parent.parent
        self.files_created: List[str] = []
        self.errors: List[str] = []

    def extract_code_blocks(self, markdown_path: Path) -> Dict[str, str]:
        """Extract code blocks from markdown file.
        
        Looks for patterns like:
        ## File 1: path/to/file.py
        ```python
        ...code...
        ```
        """
        content = markdown_path.read_text()
        blocks = {}

        # Pattern: ## File N: path/file.py followed by ```python...```
        pattern = r'## File \d+: ([\w/.\_\-]+\.py)\n\n```python\n(.*?)\n```'

        for match in re.finditer(pattern, content, re.DOTALL):
            file_path = match.group(1)
            code = match.group(2)
            blocks[file_path] = code

        return blocks

    def create_files(self, blocks: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """Create files from code blocks.
        
        Returns:
            (created_files, errors)
        """
        created = []
        errors = []

        for file_path_str, code in blocks.items():
            try:
                file_path = self.repo_root / file_path_str

                # Create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Check if file already exists
                if file_path.exists() and not self.dry_run:
                    print(f"⚠  {file_path_str} already exists (skipping)")
                    continue

                # Write file
                if not self.dry_run:
                    file_path.write_text(code, encoding="utf-8")

                created.append(file_path_str)
                print(f"✓ {file_path_str}")

            except Exception as e:
                error = f"Failed to create {file_path_str}: {e}"
                errors.append(error)
                print(f"✗ {error}")

        return created, errors

    def validate_python_syntax(self, file_path: Path) -> bool:
        """Check if a Python file has valid syntax."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                compile(f.read(), str(file_path), "exec")
            return True
        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
            return False

    def bootstrap_phase_0_1(self) -> bool:
        """Bootstrap Phase 0-1: Contracts + Registry.
        
        Returns:
            True if successful
        """
        print("\n🚀 Bootstrapping Phase 0-1: Contracts + Registry\n")

        plan_file = self.repo_root / "docs" / "Phase_0_1_Bootstrap_Code.md"

        if not plan_file.exists():
            print(f"❌ Plan file not found: {plan_file}")
            return False

        blocks = self.extract_code_blocks(plan_file)

        if not blocks:
            print(f"⚠  No code blocks found in {plan_file}")
            return False

        print(f"📋 Found {len(blocks)} code blocks\n")

        created, errors = self.create_files(blocks)

        if errors:
            print(f"\n⚠  {len(errors)} errors encountered:")
            for error in errors:
                print(f"  - {error}")

        # Validate syntax
        print("\n🔍 Validating Python syntax...")
        syntax_ok = True
        for file_path_str in created:
            file_path = self.repo_root / file_path_str
            if file_path.suffix == ".py" and file_path.exists():
                if self.validate_python_syntax(file_path):
                    print(f"✓ {file_path_str}")
                else:
                    print(f"✗ {file_path_str}")
                    syntax_ok = False

        if not syntax_ok:
            return False

        # Summary
        print(f"\n✅ Phase 0-1 bootstrap complete!")
        print(f"📁 Created {len(created)} files")

        # Write manifest
        manifest_file = self.repo_root / "BOOTSTRAP_MANIFEST.txt"
        manifest_file.write_text("\n".join(created), encoding="utf-8")
        print(f"📄 Manifest written to: {manifest_file.relative_to(self.repo_root)}")

        return len(errors) == 0

    def run(self, phase: str) -> int:
        """Run bootstrap for the specified phase.
        
        Returns:
            0 if successful, 1 on error
        """
        if phase == "phase-0-1-contracts":
            success = self.bootstrap_phase_0_1()
        else:
            print(f"❌ Unknown phase: {phase}")
            print(f"   Available phases: phase-0-1-contracts")
            return 1

        return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(
        description="Auto-bootstrap Agentic + LangChain toolbox code"
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["phase-0-1-contracts"],
        help="Bootstrap phase to generate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing files",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing files, don't create new ones",
    )

    args = parser.parse_args()

    gen = BootstrapGenerator(dry_run=args.dry_run)
    exit_code = gen.run(args.phase)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
