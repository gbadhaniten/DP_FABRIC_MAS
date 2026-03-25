# 🚀 GITHUB DEPLOYMENT GUIDE — Fabric-MAS

## Repository Details

| Field | Value |
|-------|-------|
| **GitHub User** | `gbadhaniten` |
| **Repository** | `DP_FABRIC_MAS` |
| **Branch** | `feature/mas/dev_v1` |
| **URL** | https://github.com/gbadhaniten/DP_FABRIC_MAS/tree/feature/mas/dev_v1 |

## Overview

This guide covers deploying the Fabric-MAS codebase from your local machine to GitHub,
handling the dual-account setup where you use:

- **`_AZR` account** → Microsoft Fabric / Azure operations (Fabric CLI authentication)
- **`@ten` account (`gbadhaniten`)** → GitHub repository hosting and GitHub Copilot licence

---

## Prerequisites

| Tool | Purpose | Check |
|------|---------|-------|
| Git | Version control | `git --version` |
| GitHub CLI (optional) | Easy repo creation | `gh --version` |
| VS Code | IDE with Copilot | Open VS Code |
| GitHub Copilot licence | LLM for MCP tools | Active on `@ten` account |

---

## Step-by-Step Deployment

### Step 1: Configure Git Identity for @ten Account

Open a terminal in the FABRIC-MAS folder and set your Git identity:

```powershell
# Navigate to project folder
cd "c:\Users\gbadhani\OneDrive - TEN\Technip-GB\Work\Data Delivery\Fabric\Fabric Multi-Agent System\FABRIC-MAS"

# Set Git user for THIS repository (use @ten account details)
git config user.name "Your Name"
git config user.email "your.name@ten.com"
```

> **Note:** Using `git config` (without `--global`) sets the identity for this repo only,
> so your other repos can use different accounts.

---

### Step 2: Initialize the Git Repository

```powershell
# Initialize git
git init

# Verify .gitignore is present (it should already exist)
Test-Path .gitignore   # Should return True

# Stage all files
git add .

# Create initial commit
git commit -m "feat: Fabric-MAS v2.0 — Copilot-native multi-agent system

- 49 agents (48 Fabric items + data modeling) with knowledge files
- Copilot-native: no OpenAI API key required
- 8 MCP tools for VS Code integration
- Keyword-based intelligent routing
- Auto-learning with prompt logging
- Visual workflow renderer (Rich + HTML)
- One-prompt setup wizard"
```

---

### Step 3: Connect to Existing Repository

The repository already exists at https://github.com/gbadhaniten/DP_FABRIC_MAS

```powershell
# Add the remote
git remote add origin https://github.com/gbadhaniten/DP_FABRIC_MAS.git

# Fetch remote branches
git fetch origin

# Checkout the feature branch
git checkout -b feature/mas/dev_v1

# Push all artifacts to the feature branch
git push -u origin feature/mas/dev_v1
```

> **Merge strategy:** Once all artifacts are validated on `feature/mas/dev_v1`,
> create a Pull Request to merge into `main`.

---

### Step 4: Handle Dual-Account Authentication

Since you use `_AZR` for Fabric and `@ten` for GitHub, you need separate auth contexts.

#### GitHub Authentication (@ten account)

```powershell
# Option 1: HTTPS with credential manager (recommended for Windows)
git config credential.helper manager

# When you push, Windows will prompt for @ten GitHub credentials
# These get stored in Windows Credential Manager

# Option 2: SSH key (more permanent)
ssh-keygen -t ed25519 -C "your.name@ten.com" -f "$env:USERPROFILE\.ssh\id_ed25519_ten"

# Add the public key to your @ten GitHub account:
# GitHub.com → Settings → SSH Keys → New SSH Key
Get-Content "$env:USERPROFILE\.ssh\id_ed25519_ten.pub" | Set-Clipboard

# Configure SSH for this repo
git remote set-url origin git@github.com:YOUR_TEN_USERNAME/FABRIC-MAS.git
```

#### Fabric CLI Authentication (_AZR account)

```powershell
# This is completely separate from GitHub auth
# Fabric CLI uses Azure AD / Entra ID authentication
fab auth login

# This opens a browser where you sign in with your _AZR account
# The token is stored locally by the Fabric CLI
```

> **Key Point:** Git (GitHub) and Fabric CLI use completely separate authentication.
> - Git → `@ten` credentials (GitHub username/token)
> - `fab` CLI → `_AZR` credentials (Azure AD/Entra ID)

---

### Step 5: Verify Everything Works

```powershell
# Check Git remote is set
git remote -v
# Should show: origin https://github.com/gbadhaniten/DP_FABRIC_MAS.git

# Check current branch
git branch
# Should show: * feature/mas/dev_v1

# Check Fabric CLI auth (uses _AZR account)
fab auth status

# Check GitHub Copilot in VS Code (uses @ten/gbadhaniten account)
# Open Copilot Chat → should show your identity
```

---

## Team Collaboration

### For Team Members to Get Started

```powershell
# 1. Clone the repo (using @ten GitHub account)
git clone https://github.com/gbadhaniten/DP_FABRIC_MAS.git
cd DP_FABRIC_MAS

# 2. Run the one-prompt setup wizard
python setup_wizard.py

# 3. Authenticate Fabric CLI (using their _AZR account)
fab auth login

# 4. Open in VS Code — Copilot will auto-discover MCP tools
code .
```

### Branch Strategy

```
main                      ← stable, production-ready
└── feature/mas/dev_v1    ← current development (all Fabric-MAS artifacts)
    ├── (merge to main via Pull Request after validation)
    │
    Future branches:
    ├── feature/mas/new-agent       ← adding new agents
    ├── feature/mas/model-updates   ← data modeling guidelines
    └── fix/mas/agent-bug           ← bug fixes
```

```powershell
# Current workflow: work on feature/mas/dev_v1
git checkout feature/mas/dev_v1
# ... make changes ...
git add .
git commit -m "feat: description of change"
git push

# When ready: create Pull Request on GitHub to merge into main
# URL: https://github.com/gbadhaniten/DP_FABRIC_MAS/compare/main...feature/mas/dev_v1
```

---

## Updating the Repo

### Regular Workflow

```powershell
# Check status
git status

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new data modeling guidelines for HR domain"

# Push to GitHub
git push
```

### After Agent Knowledge Updates

When agents auto-learn (examples.md gets updated), commit those changes periodically:

```powershell
# See what changed
git diff fabric_mas/agents/*/examples.md

# Commit learned patterns
git add fabric_mas/agents/*/examples.md
git commit -m "chore: auto-learned patterns from agent executions"
git push
```

---

## CI/CD (Optional)

### GitHub Actions Workflow

Create `.github/workflows/validate.yml` for automated testing:

```yaml
name: Validate Fabric-MAS
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate imports
        run: |
          python -c "from fabric_mas.core.orchestrator import Orchestrator; print('OK')"
          python -c "from fabric_mas.core.base_agent import BaseAgent; print('OK')"
      - name: Count agents
        run: |
          python -c "
          from fabric_mas.core.orchestrator import Orchestrator
          o = Orchestrator()
          o.auto_register()
          count = len(o.registry.list_agents())
          print(f'Registered {count} agents')
          assert count >= 48, f'Expected 48+ agents, got {count}'
          "
```

---

## Security Notes

1. **Never commit `.env`** — it may contain API keys (already in `.gitignore`)
2. **Fabric CLI tokens** are stored locally by the `fab` CLI, not in the repo
3. **GitHub Copilot licence** is tied to your `@ten` VS Code login, not the repo
4. For team use, consider adding a `.env.example` with placeholder values (already included)
5. If you use SSH keys, ensure they're password-protected

---

## Quick Reference

| Action | Command |
|--------|---------|
| Setup from scratch | `python setup_wizard.py` |
| Push changes | `git add . ; git commit -m "msg" ; git push` |
| Fabric CLI login | `fab auth login` (uses _AZR account) |
| GitHub login | `gh auth login` (uses gbadhaniten account) |
| Run MCP server | `python mcp_server.py` |
| Check system | In Copilot Chat: "Check Fabric-MAS system status" |
| View repo | https://github.com/gbadhaniten/DP_FABRIC_MAS |
| View branch | https://github.com/gbadhaniten/DP_FABRIC_MAS/tree/feature/mas/dev_v1 |
| Create PR | https://github.com/gbadhaniten/DP_FABRIC_MAS/compare/main...feature/mas/dev_v1 |
