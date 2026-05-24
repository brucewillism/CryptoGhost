# GitHub Release Guide

Step-by-step instructions to publish CryptoGhost v5.0.0 to GitHub.

## Pre-Release Checklist

```bash
python scripts/scan_secrets.py --strict
python scripts/pre_release_check.py
pytest tests/ -v
```

Verify:
- [ ] `.env` is NOT staged (`git status` should not show `.env`)
- [ ] No real API keys in any file
- [ ] `.env.example` uses placeholders only
- [ ] All 75+ tests pass

## 1. Initialize Git Repository

```bash
cd CryptoGhost

git init
git branch -M main
```

## 2. Stage and Commit

```bash
git add .
git status   # VERIFY .env is NOT listed

git commit -m "$(cat <<'EOF'
feat: initial CryptoGhost v5 release

Self-Improving Institutional Quantitative AI Platform with
multi-agent intelligence (v2), quant infrastructure (v3),
investment prioritization (v4), and self-improving engine (v5).

EOF
)"
```

## 3. Create GitHub Repository

**Option A — GitHub CLI:**
```bash
gh repo create CryptoGhost --public --description "Self-Improving Institutional Quantitative AI Platform" --source=. --remote=origin
git push -u origin main
```

**Option B — Manual:**
1. Go to https://github.com/new
2. Name: `CryptoGhost`
3. Description: `Self-Improving Institutional Quantitative AI Platform`
4. Public, no README/license (already in repo)
5. Create repository
6. Connect remote:

```bash
git remote add origin https://github.com/YOUR_USERNAME/CryptoGhost.git
git push -u origin main
```

## 4. Create Release v5.0.0

```bash
gh release create v5.0.0 \
  --title "CryptoGhost v5 — Self-Improving Institutional AI" \
  --notes-file CHANGELOG.md
```

Or via GitHub UI: **Releases → Draft new release → Tag v5.0.0**

## 5. Configure Repository Settings

Recommended GitHub settings:

- **Settings → Secrets and variables → Actions**: add any CI secrets
- **Settings → Security → Dependabot**: enable for pip and npm
- **Settings → Branches**: protect `main` (require PR + CI pass)
- **Settings → General**: enable Issues and Discussions

## 6. Update README Badges

After creating the repo, update badge URLs in `README.md`:

```markdown
[![CI](https://github.com/YOUR_USERNAME/CryptoGhost/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

## 7. Post-Release

```bash
# Verify CI passed
gh run list --limit 5

# Tag locally
git tag -l
```

## Security Reminder

If you accidentally committed secrets:

```bash
# Remove from history (destructive — coordinate with team)
git filter-repo --path .env --invert-paths
# Rotate ALL exposed keys immediately
```

Never force-push to main without understanding the impact.
