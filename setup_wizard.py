"""
setup_wizard.py — One-Prompt Setup for Fabric-MAS
====================================================
Run this script to configure the entire Fabric-MAS system in one step.
It handles: dependency installation, .env creation, Fabric CLI auth,
MCP configuration for VS Code, and system validation.

Usage from VS Code Copilot:
    "Set up Fabric-MAS" → Copilot runs this script automatically

Usage from terminal:
    python setup_wizard.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Colours for terminal output
# ---------------------------------------------------------------------------
class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {C.GREEN}✅ {msg}{C.RESET}")


def warn(msg: str) -> None:
    print(f"  {C.YELLOW}⚠️  {msg}{C.RESET}")


def fail(msg: str) -> None:
    print(f"  {C.RED}❌ {msg}{C.RESET}")


def info(msg: str) -> None:
    print(f"  {C.CYAN}ℹ  {msg}{C.RESET}")


def header(msg: str) -> None:
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {msg}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}")


# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Step 1: Check Python version
# ---------------------------------------------------------------------------
def check_python() -> bool:
    header("Step 1/7: Checking Python Version")
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 10:
        ok(f"Python {major}.{minor} detected (3.10+ required)")
        return True
    else:
        fail(f"Python {major}.{minor} detected — need 3.10+")
        return False


# ---------------------------------------------------------------------------
# Step 2: Create virtual environment
# ---------------------------------------------------------------------------
def setup_venv() -> bool:
    header("Step 2/7: Setting Up Virtual Environment")
    venv_path = PROJECT_ROOT / ".venv"

    if venv_path.exists():
        ok(f"Virtual environment already exists at {venv_path}")
        return True

    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True, capture_output=True,
        )
        ok(f"Created virtual environment at {venv_path}")

        # Determine pip path
        if os.name == "nt":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"

        info(f"Pip located at: {pip_path}")
        return True
    except subprocess.CalledProcessError as e:
        fail(f"Failed to create venv: {e}")
        return False


# ---------------------------------------------------------------------------
# Step 3: Install dependencies
# ---------------------------------------------------------------------------
def install_deps() -> bool:
    header("Step 3/7: Installing Dependencies")
    venv_path = PROJECT_ROOT / ".venv"

    if os.name == "nt":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"

    # Use the venv python if available, otherwise system python
    pip_cmd = str(pip_path) if pip_path.exists() else f"{sys.executable} -m pip"
    req_file = PROJECT_ROOT / "requirements.txt"

    if not req_file.exists():
        fail("requirements.txt not found!")
        return False

    try:
        if pip_path.exists():
            subprocess.run(
                [str(pip_path), "install", "-r", str(req_file)],
                check=True, capture_output=True, text=True,
            )
        else:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                check=True, capture_output=True, text=True,
            )
        ok("All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        fail(f"Dependency installation failed: {e.stderr[:200] if e.stderr else str(e)}")
        warn("Try manually: pip install -r requirements.txt")
        return False


# ---------------------------------------------------------------------------
# Step 4: Create .env file
# ---------------------------------------------------------------------------
def setup_env() -> bool:
    header("Step 4/7: Configuring Environment (.env)")
    env_file = PROJECT_ROOT / ".env"
    example_file = PROJECT_ROOT / ".env.example"

    if env_file.exists():
        ok(".env file already exists")
        info("Edit .env to update configuration if needed")
        return True

    if example_file.exists():
        shutil.copy(str(example_file), str(env_file))
        ok("Created .env from .env.example")
        info("No OpenAI API key needed — GitHub Copilot is the LLM!")
        info("Optional: Add TAVILY_API_KEY for auto-train documentation search")
        info("Optional: Set FABRIC_WORKSPACE_ID for default workspace")
        return True
    else:
        # Create minimal .env
        env_content = (
            "# Fabric-MAS Environment\n"
            "# No OpenAI API key needed — GitHub Copilot is the LLM!\n\n"
            "TAVILY_API_KEY=\n"
            "BING_SEARCH_API_KEY=\n"
            "FABRIC_WORKSPACE_ID=\n"
            "FABRIC_DRY_RUN=true\n"
        )
        env_file.write_text(env_content, encoding="utf-8")
        ok("Created minimal .env file")
        return True


# ---------------------------------------------------------------------------
# Step 5: Check Fabric CLI
# ---------------------------------------------------------------------------
def check_fabric_cli() -> bool:
    header("Step 5/7: Checking Microsoft Fabric CLI")

    # Check if fab is available
    fab_path = shutil.which("fab")
    if fab_path:
        ok(f"Fabric CLI found at: {fab_path}")
        # Check auth status
        try:
            result = subprocess.run(
                ["fab", "auth", "status"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                ok("Fabric CLI is authenticated")
            else:
                warn("Fabric CLI not authenticated — run: fab auth login")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            warn("Could not check auth status — run: fab auth login")
        return True
    else:
        warn("Fabric CLI not found in PATH")
        info("Install with: pip install ms-fabric-cli")
        info("Then authenticate: fab auth login")
        return False


# ---------------------------------------------------------------------------
# Step 6: Configure MCP for VS Code
# ---------------------------------------------------------------------------
def setup_mcp() -> bool:
    header("Step 6/7: Configuring MCP for VS Code")
    vscode_dir = PROJECT_ROOT / ".vscode"
    mcp_file = vscode_dir / "mcp.json"

    # Determine the Python executable path
    venv_path = PROJECT_ROOT / ".venv"
    if os.name == "nt":
        python_path = str(venv_path / "Scripts" / "python.exe")
    else:
        python_path = str(venv_path / "bin" / "python")

    # Fallback to system python if venv doesn't exist
    if not Path(python_path).exists():
        python_path = sys.executable

    mcp_config = {
        "servers": {
            "fabric-mas": {
                "type": "stdio",
                "command": python_path,
                "args": ["mcp_server.py"],
                "cwd": str(PROJECT_ROOT),
            }
        }
    }

    vscode_dir.mkdir(exist_ok=True)

    if mcp_file.exists():
        ok("MCP configuration already exists")
        # Update it anyway
        info("Updating .vscode/mcp.json with current paths")

    mcp_file.write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")
    ok(f"Created .vscode/mcp.json")
    info(f"Python path: {python_path}")
    info("MCP server will auto-start when Copilot sends its first request")
    return True


# ---------------------------------------------------------------------------
# Step 7: Validate system
# ---------------------------------------------------------------------------
def validate_system() -> bool:
    header("Step 7/7: Validating System")
    all_ok = True

    # Check core imports
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from fabric_mas.core.base_agent import BaseAgent
        ok("Core module imports: ✓")
    except ImportError as e:
        fail(f"Core import failed: {e}")
        all_ok = False

    try:
        from fabric_mas.core.orchestrator import Orchestrator
        ok("Orchestrator import: ✓")
    except ImportError as e:
        fail(f"Orchestrator import failed: {e}")
        all_ok = False

    # Count agents
    agents_dir = PROJECT_ROOT / "fabric_mas" / "agents"
    if agents_dir.is_dir():
        agent_folders = [
            d for d in agents_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_") and (d / "agent.py").exists()
        ]
        ok(f"Agent folders found: {len(agent_folders)}")
    else:
        fail("Agents directory not found!")
        all_ok = False

    # Check MCP config
    mcp_file = PROJECT_ROOT / ".vscode" / "mcp.json"
    if mcp_file.exists():
        ok("MCP configuration: ✓")
    else:
        warn("MCP configuration missing — run setup again")

    # Check .env
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        ok("Environment file (.env): ✓")
    else:
        warn(".env not found — create from .env.example")

    return all_ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"\n{C.BOLD}{C.CYAN}")
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║   🏭 Fabric-MAS Setup Wizard                    ║")
    print("  ║   Copilot-Native Multi-Agent System              ║")
    print("  ║   No OpenAI API Key Required!                    ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    results = {}
    results["python"] = check_python()
    results["venv"] = setup_venv()
    results["deps"] = install_deps()
    results["env"] = setup_env()
    results["fabric_cli"] = check_fabric_cli()
    results["mcp"] = setup_mcp()
    results["validate"] = validate_system()

    # Summary
    header("Setup Complete!")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for step, ok_val in results.items():
        icon = "✅" if ok_val else "❌"
        print(f"  {icon} {step}")

    print()
    if passed == total:
        print(f"  {C.GREEN}{C.BOLD}🎉 All {total} steps passed! Fabric-MAS is ready.{C.RESET}")
        print()
        print(f"  {C.CYAN}Next steps:{C.RESET}")
        print(f"  1. Open VS Code in this folder")
        print(f"  2. Open GitHub Copilot Chat (Ctrl+Shift+I)")
        print(f"  3. Type: {C.BOLD}@workspace Create a lakehouse called Bronze{C.RESET}")
        print(f"  4. Copilot will use Fabric-MAS MCP tools automatically!")
    else:
        print(f"  {C.YELLOW}{passed}/{total} steps passed.{C.RESET}")
        print(f"  Fix the failed steps above and re-run: {C.BOLD}python setup_wizard.py{C.RESET}")

    print()


if __name__ == "__main__":
    main()
