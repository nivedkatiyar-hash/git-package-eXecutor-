#!/usr/bin/env python3
"""
gpx - Professional GitHub Package Manager
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
import json
from pathlib import Path

# Paths
GPX_HOME = Path.home() / ".local" / "share" / "gpx"
EXT_DIR = Path.home() / ".local" / "share" / "gpx-extensions"
BIN_DIR = Path.home() / ".local" / "bin"

# UI Colors
C_BLUE, C_GREEN, C_YELLOW, C_RED, C_DIM, C_RESET, C_CLEAR = \
    "\033[94m", "\033[92m", "\033[93m", "\033[91m", "\033[2m", "\033[0m", "\033[K"

def log_info(msg): print(f"{C_BLUE}ℹ{C_RESET} {msg}")
def log_success(msg): print(f"{C_GREEN}✔{C_RESET} {msg}")
def log_error(msg): print(f"{C_RED}✖{C_RESET} {msg}", file=sys.stderr)

def get_run_command(target_dir):
    """Read gpx.json for custom run instructions."""
    config_file = target_dir / "gpx.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f).get("run", "python3 main.py")
        except: pass
    return "python3 main.py"

def animate_spinner(stop_event, text):
    spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{C_BLUE}{spinners[i]}{C_RESET} {text}")
        sys.stdout.flush()
        i = (i + 1) % len(spinners)
        time.sleep(0.08)
    sys.stdout.write(f"\r{C_CLEAR}")

def run_task(cmd, text, cwd=None):
    stop = threading.Event()
    thread = threading.Thread(target=animate_spinner, args=(stop, text))
    thread.start()
    try:
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        stop.set()
        thread.join()
    except Exception as e:
        stop.set()
        thread.join()
        log_error(f"Task failed: {e}")
        sys.exit(1)

# --- APP MANAGEMENT ---

def app_install(repo):
    repo_name = repo.split("/")[-1]
    target_dir = GPX_HOME / repo_name
    if target_dir.exists():
        log_error(f"'{repo_name}' is already installed.")
        sys.exit(1)
    
    run_task(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(target_dir)], f"Downloading {repo}...")
    
    # Create symlink
    symlink = BIN_DIR / repo_name
    if symlink.exists(): symlink.unlink()
    # Note: Simplified symlink to wrapper logic
    symlink.symlink_to(target_dir) 
    log_success(f"Installed {repo_name}. Config: {get_run_command(target_dir)}")

def app_uninstall(repo_name):
    target_dir = GPX_HOME / repo_name
    if target_dir.exists():
        shutil.rmtree(target_dir)
        (BIN_DIR / repo_name).unlink(missing_ok=True)
        log_success(f"Removed {repo_name}")

# --- PLUGIN MANAGEMENT ---

def plugin_install(repo):
    repo_name = repo.split("/")[-1]
    run_task(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(EXT_DIR / repo_name)], f"Installing plugin {repo}...")
    log_success(f"Plugin '{repo_name}' installed.")

# --- MAIN ---

def main():
    GPX_HOME.mkdir(parents=True, exist_ok=True)
    EXT_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="gpx - Professional Package Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # App Commands
    app = subparsers.add_parser("app")
    app_sub = app.add_subparsers(dest="action", required=True)
    app_sub.add_parser("install").add_argument("repo")
    app_sub.add_parser("uninstall").add_argument("name")
    
    # Plugin Commands
    plugin = subparsers.add_parser("plugin")
    plugin_sub = plugin.add_subparsers(dest="action", required=True)
    plugin_sub.add_parser("install").add_argument("repo")

    args = parser.parse_args()

    if args.command == "app":
        if args.action == "install": app_install(args.repo)
        if args.action == "uninstall": app_uninstall(args.name)
    elif args.command == "plugin":
        if args.action == "install": plugin_install(args.repo)

if __name__ == "__main__":
    main()
