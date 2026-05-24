#!/usr/bin/env python3
"""
CryptoGhost — Scanner de segredos para pré-release.

Detecta API keys, tokens, passwords e URLs privadas antes do push.
Uso: python scripts/scan_secrets.py [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", "dist", "build", "htmlcov",
}
SKIP_FILES = {".env", ".env.local", ".env.production"}
SCAN_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml",
    ".md", ".toml", ".ini", ".env.example", ".sh", ".sql",
}

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenAI API Key", re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("Anthropic API Key", re.compile(r"sk-ant-[a-zA-Z0-9\-_]{20,}")),
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub Token", re.compile(r"ghp_[a-zA-Z0-9]{36,}")),
    ("GitHub OAuth", re.compile(r"gho_[a-zA-Z0-9]{36,}")),
    ("Generic Bearer Token", re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}")),
    ("Private IP (Ollama/infra)", re.compile(r"http://(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d+\.\d+")),
    ("Public IP hardcoded", re.compile(r"http://(?:\d{1,3}\.){3}\d{1,3}:\d+")),
    ("Hardcoded password", re.compile(r"(?i)(password|passwd|secret)\s*[=:]\s*['\"][^'\"]{8,}['\"]")),
    ("JWT hardcoded", re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")),
]

ALLOWLIST_FILES = {".env.example", "scan_secrets.py", "pre_release_check.py"}
ALLOWLIST_PATTERNS = [
    re.compile(r"change-me", re.I),
    re.compile(r"your-ollama-host", re.I),
    re.compile(r"localhost", re.I),
    re.compile(r"127\.0\.0\.1", re.I),
    re.compile(r"example\.com", re.I),
    re.compile(r"placeholder", re.I),
    re.compile(r"sk-\.\.\.", re.I),
]


def should_skip_path(path: Path) -> bool:
    if path.name in SKIP_FILES:
        return True
    if path.name in ALLOWLIST_FILES and path.suffix != ".py":
        return False
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    if path.suffix and path.suffix not in SCAN_EXTENSIONS and path.name not in ALLOWLIST_FILES:
        return True
    return False


def is_allowlisted(line: str) -> bool:
    return any(p.search(line) for p in ALLOWLIST_PATTERNS)


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for line_no, line in enumerate(content.splitlines(), 1):
        if is_allowlisted(line):
            continue
        for name, pattern in PATTERNS:
            if pattern.search(line):
                if path.name == ".env.example" and "change-me" in line.lower():
                    continue
                findings.append((line_no, name, line.strip()[:120]))
    return findings


def check_gitignore() -> list[str]:
    issues: list[str] = []
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        issues.append(".gitignore não encontrado")
        return issues
    content = gitignore.read_text(encoding="utf-8")
    for required in [".env", "node_modules", "__pycache__", ".venv"]:
        if required not in content:
            issues.append(f".gitignore não ignora: {required}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="CryptoGhost secret scanner")
    parser.add_argument("--strict", action="store_true", help="Falha em IPs públicos hardcoded")
    args = parser.parse_args()

    print("CryptoGhost — Secret Scanner\n")
    all_findings: list[tuple[Path, int, str, str]] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or should_skip_path(path):
            continue
        for line_no, name, snippet in scan_file(path):
            if name == "Public IP hardcoded" and not args.strict:
                if path.name == ".env":
                    continue
            all_findings.append((path.relative_to(ROOT), line_no, name, snippet))

    gitignore_issues = check_gitignore()
    if gitignore_issues:
        print("[FAIL] Problemas no .gitignore:")
        for issue in gitignore_issues:
            print(f"  - {issue}")
    else:
        print("[OK] .gitignore configurado corretamente")

    env_file = ROOT / ".env"
    if env_file.exists():
        print("[INFO] .env existe localmente (deve permanecer fora do Git)")

    if all_findings:
        print(f"\n[FAIL] {len(all_findings)} possível(is) segredo(s) encontrado(s):\n")
        for path, line_no, name, snippet in all_findings:
            print(f"  {path}:{line_no} [{name}]")
            print(f"    {snippet}\n")
        return 1

    print("\n[OK] Nenhum segredo detectado — repositório seguro para push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
