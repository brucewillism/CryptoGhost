#!/usr/bin/env python3
"""CryptoGhost — Pre-release validation checklist."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECKS = [
    ("Secret scanner", [sys.executable, "scripts/scan_secrets.py"]),
    ("Pytest suite", [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"]),
]

REQUIRED_FILES = [
    ".gitignore",
    ".env.example",
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "start_dev.py",
    ".github/workflows/ci.yml",
]

FORBIDDEN_IN_GIT = [".env"]


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def main() -> int:
    print("\nCryptoGhost v5.0 — Pre-Release Checklist\n")
    print("=" * 50)
    errors = 0

    print("\n[1] Required files")
    for f in REQUIRED_FILES:
        if (ROOT / f).exists():
            ok(f)
        else:
            fail(f"Missing: {f}")
            errors += 1

    print("\n[2] Sensitive files protection")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    for f in FORBIDDEN_IN_GIT:
        if f in gitignore:
            ok(f"{f} in .gitignore")
        else:
            fail(f"{f} NOT in .gitignore")
            errors += 1

    print("\n[3] Automated checks")
    for name, cmd in CHECKS:
        print(f"  Running {name}...")
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            ok(name)
        else:
            fail(name)
            if result.stdout:
                print(result.stdout[-500:])
            if result.stderr:
                print(result.stderr[-500:])
            errors += 1

    print("\n" + "=" * 50)
    if errors == 0:
        print("RELEASE READY — All checks passed\n")
        print("Next steps:")
        print("  git init")
        print('  git add .')
        print('  git commit -m "feat: initial CryptoGhost v5 release"')
        print("  gh repo create CryptoGhost --public --source=. --push")
        print('  gh release create v5.0.0 --title "CryptoGhost v5 — Self-Improving Institutional AI" --notes-file CHANGELOG.md')
        return 0

    print(f"NOT READY — {errors} check(s) failed\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
