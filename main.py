#!/usr/bin/env python3
"""
gpx - A lightweight pipx-like installer for GitHub repositories with extensions.
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

# Configuration paths
GPX_HOME = Path.home() / ".local" / "share" / "gpx"
EXT_DIR = Path.home() / ".local" / "share" / "gpx-extensions"
BIN_DIR = Path.home() / ".local" / "bin"

# Terminal Colors
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"
C_CLEAR_LINE = "\033[K"

def setup_environment():
    """Ensure our target directories exist."""
    GPX_HOME.mkdir(parents=True, exist_ok=True)
    EXT_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    
    if str(BIN_DIR) not in os.environ.get("PATH", ""):
        print(f"{C_YELLOW}Warning: {BIN_DIR} is not in your PATH.{C_RESET}")
        print(f"Add 'export PATH=\"$HOME/.local/bin:$PATH\"' to your shell profile.\n")

# --- UI VISUALS ---

def animate_spinner(stop_event, text):
    """Runs a smooth spinner animation in the terminal."""
    # Braille spinner pattern (standard in modern CLIs)
    spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{C_BLUE}{spinners[i]}{C_RESET} {text}")
        sys.stdout.flush()
        i = (i + 1) % len(spinners)
        time.sleep(0.08)
    # Clear the line when done
    sys.stdout.write(f"\r{C_CLEAR_LINE}")
    sys.stdout.flush()

def run_command_with_ui(cmd, ui_text, cwd=None, exit_on_fail=True):
    """Runs a command silently in the background while showing a UI spinner."""
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=animate_spinner, args=(stop_event, ui_text))
    spinner_thread.start()

    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stop_event.set()
        spinner_thread.join()
        return result
    except subprocess.CalledProcessError as e:
        stop_event.set()
        spinner_thread.join()
        if exit_on_fail:
            print(f"{C_RED}✖ Error executing: {' '.join(cmd)}{C_RESET}")
            print(f"{C_DIM}{e.stderr.strip()}{C_RESET}")
            sys.exit(1)
        return None

# --- CORE APP MANAGEMENT ---

def install(repo, executable_name=None):
    if "/" not in repo:
        print(f"{C_RED}Error: Repository must be in 'user/repo' format.{C_RESET}")
        sys.exit(1)

    repo_name = repo.split("/")[-1]
    target_dir = GPX_HOME / repo_name

    if target_dir.exists():
        print(f"{C_YELLOW}Repository '{repo_name}' is already installed.{C_RESET}")
        print(f"Use 'gpx update {repo_name}' to get the latest version.")
        sys.exit(1)

    clone_url = f"https://github.com/{repo}.git"
    run_command_with_ui(["git", "clone", "--depth", "1", clone_url, str(target_dir)], f"Downloading {repo}...")

    exec_target = target_dir / (executable_name or repo_name)
    
    if not exec_target.exists():
        fallbacks = [f"{repo_name}.py", f"{repo_name}.sh", "main.py", "run.sh", "app.py"]
        for fallback in fallbacks:
            if (target_dir / fallback).exists():
                exec_target = target_dir / fallback
                break

    if exec_target.exists():
        exec_target.chmod(exec_target.stat().st_mode | 0o111)
        symlink_path = BIN_DIR / repo_name
        if symlink_path.exists():
            symlink_path.unlink()
        symlink_path.symlink_to(exec_target)
        print(f"{C_GREEN}✔ Installed successfully!{C_RESET}")
        print(f"Run it globally using: {C_BLUE}{repo_name}{C_RESET}")
    else:
        print(f"{C_YELLOW}⚠ Cloned {repo_name}, but no executable found.{C_RESET}")
        print("Use the --exec flag to specify the file next time.")

def remove(repo_name):
    target_dir = GPX_HOME / repo_name
    symlink_path = BIN_DIR / repo_name

    if not target_dir.exists():
        print(f"{C_RED}Error: '{repo_name}' is not installed.{C_RESET}")
        sys.exit(1)

    print(f"{C_DIM}Removing '{repo_name}'...{C_RESET}")
    shutil.rmtree(target_dir)
    
    if symlink_path.exists() and symlink_path.is_symlink():
        symlink_path.unlink()
    print(f"{C_GREEN}✔ Removed.{C_RESET}")

def update(repo_name):
    target_dir = GPX_HOME / repo_name
    if not target_dir.exists():
        target_dir = EXT_DIR / repo_name
        if not target_dir.exists():
            print(f"{C_RED}Error: '{repo_name}' is not installed.{C_RESET}")
            sys.exit(1)

    run_command_with_ui(["git", "pull"], f"Updating {repo_name}...", cwd=target_dir)
    print(f"{C_GREEN}✔ '{repo_name}' is now up to date.{C_RESET}")

def list_repos():
    print(f"{C_BLUE}--- Apps ---{C_RESET}")
    if GPX_HOME.exists() and any(GPX_HOME.iterdir()):
        for item in GPX_HOME.iterdir():
            if item.is_dir() and (item / ".git").exists():
                print(f"  📦 {item.name}")
    else:
        print(f"  {C_DIM}(No apps installed){C_RESET}")

    print(f"\n{C_BLUE}--- Extensions ---{C_RESET}")
    if EXT_DIR.exists() and any(EXT_DIR.iterdir()):
        for item in EXT_DIR.iterdir():
            if item.is_dir() and (item / ".git").exists():
                print(f"  🔌 {item.name}")
    else:
        print(f"  {C_DIM}(No extensions installed){C_RESET}")

def create(project_name):
    project_dir = Path.cwd() / project_name
    if project_dir.exists():
        print(f"{C_RED}Error: Directory '{project_name}' already exists.{C_RESET}")
        sys.exit(1)
        
    project_dir.mkdir()
    
    entry_file = project_dir / f"{project_name}.py"
    entry_code = f'''#!/usr/bin/env python3\nimport sys\ndef main():\n    print("Hello from {project_name}!")\nif __name__ == "__main__":\n    main()'''
    entry_file.write_text(entry_code)
    entry_file.chmod(entry_file.stat().st_mode | 0o111)

    run_file = project_dir / "run.sh"
    run_code = f'''#!/usr/bin/env bash\nDIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"\ncd "$DIR" || exit 1\n./{project_name}.py "$@"'''
    run_file.write_text(run_code)
    run_file.chmod(run_file.stat().st_mode | 0o111)

    print(f"{C_GREEN}✔ Successfully generated app template at './{project_name}/'{C_RESET}")

# --- EXTENSION MANAGEMENT ---

def ext_install(repo):
    if "/" not in repo:
        print(f"{C_RED}Error: Repository must be in 'user/repo' format.{C_RESET}")
        sys.exit(1)

    repo_name = repo.split("/")[-1]
    target_dir = EXT_DIR / repo_name

    if target_dir.exists():
        print(f"{C_YELLOW}Extension '{repo_name}' is already installed.{C_RESET}")
        sys.exit(1)

    clone_url = f"https://github.com/{repo}.git"
    run_command_with_ui(["git", "clone", "--depth", "1", clone_url, str(target_dir)], f"Downloading extension {repo}...")

    for py_file in target_dir.glob("*.py"):
        py_file.chmod(py_file.stat().st_mode | 0o111)

    print(f"{C_GREEN}✔ Extension '{repo_name}' installed!{C_RESET}")

def ext_remove(repo_name):
    target_dir = EXT_DIR / repo_name
    if not target_dir.exists():
        print(f"{C_RED}Error: Extension '{repo_name}' is not installed.{C_RESET}")
        sys.exit(1)

    print(f"{C_DIM}Removing extension '{repo_name}'...{C_RESET}")
    shutil.rmtree(target_dir)
    print(f"{C_GREEN}✔ Removed.{C_RESET}")

def ext_create(ext_name):
    ext_dir = Path.cwd() / ext_name
    if ext_dir.exists():
        print(f"{C_RED}Error: Directory '{ext_name}' already exists.{C_RESET}")
        sys.exit(1)
        
    ext_dir.mkdir()
    
    cmd_name = ext_name.replace("gpx-", "") if ext_name.startswith("gpx-") else ext_name
    
    entry_file = ext_dir / f"{cmd_name}.py"
    entry_code = f'''#!/usr/bin/env python3
import sys

def main():
    print("Hello from the {ext_name} extension!")
    print(f"Arguments passed: {{sys.argv[1:]}}")

if __name__ == "__main__":
    main()
'''
    entry_file.write_text(entry_code)
    entry_file.chmod(entry_file.stat().st_mode | 0o111)
    
    print(f"{C_GREEN}✔ Extension template generated at './{ext_name}/'{C_RESET}")
    print(f"The trigger command will be: {C_BLUE}gpx {cmd_name}{C_RESET}")

def find_and_run_extension(cmd_name, args):
    if not EXT_DIR.exists(): return False
        
    for item in EXT_DIR.iterdir():
        if item.is_dir():
            target_script = item / f"{cmd_name}.py"
            if target_script.exists():
                subprocess.run([str(target_script)] + args, cwd=item)
                return True
    return False

# --- MAIN DISPATCHER ---

def main():
    setup_environment()
    
    builtins = ["install", "remove", "update", "list", "create", "ext", "-h", "--help"]
    
    if len(sys.argv) > 1 and sys.argv[1] not in builtins:
        ext_command = sys.argv[1]
        ext_args = sys.argv[2:]
        if find_and_run_extension(ext_command, ext_args):
            sys.exit(0)
        else:
            print(f"{C_RED}Unknown command or extension: '{ext_command}'{C_RESET}")
            sys.exit(1)

    parser = argparse.ArgumentParser(description="gpx - A lightweight GitHub repo installer")
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="Install an app")
    install_parser.add_argument("repo")
    install_parser.add_argument("--exec", default=None)

    remove_parser = subparsers.add_parser("remove", help="Remove an app")
    remove_parser.add_argument("repo_name")

    update_parser = subparsers.add_parser("update", help="Update an app or extension")
    update_parser.add_argument("repo_name")

    subparsers.add_parser("list", help="List all apps and extensions")

    create_parser = subparsers.add_parser("create", help="Create a new app template")
    create_parser.add_argument("project_name")

    ext_parser = subparsers.add_parser("ext", help="Manage gpx extensions")
    ext_sub = ext_parser.add_subparsers(dest="ext_command")
    
    ext_install_cmd = ext_sub.add_parser("install", help="Install an extension")
    ext_install_cmd.add_argument("repo")
    
    ext_remove_cmd = ext_sub.add_parser("remove", help="Remove an extension")
    ext_remove_cmd.add_argument("repo_name")
    
    ext_create_cmd = ext_sub.add_parser("create", help="Scaffold a new extension")
    ext_create_cmd.add_argument("ext_name")

    args = parser.parse_args()

    if args.command == "install": install(args.repo, args.exec)
    elif args.command == "remove": remove(args.repo_name)
    elif args.command == "update": update(args.repo_name)
    elif args.command == "list": list_repos()
    elif args.command == "create": create(args.project_name)
    elif args.command == "ext":
        if args.ext_command == "install": ext_install(args.repo)
        elif args.ext_command == "remove": ext_remove(args.repo_name)
        elif args.ext_command == "create": ext_create(args.ext_name)
        else: ext_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
