#!/usr/bin/env python3
"""
gpx-health: Diagnoses broken links and missing files in the gpx ecosystem.
"""
import os
from pathlib import Path

C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"

GPX_HOME = Path.home() / ".local" / "share" / "gpx"
BIN_DIR = Path.home() / ".local" / "bin"

def main():
    print("Running gpx health check...\n")
    issues = 0

    if not GPX_HOME.exists() or not any(GPX_HOME.iterdir()):
        print(f"{C_DIM}No apps installed yet. System looks fine.{C_RESET}")
        return

    for item in GPX_HOME.iterdir():
        if item.is_dir():
            repo_name = item.name
            symlink_path = BIN_DIR / repo_name
            
            print(f"Checking {repo_name}...")
            
            # Check 1: Does the symlink exist?
            if not symlink_path.exists():
                print(f"  {C_RED}✖ Missing global symlink in ~/.local/bin{C_RESET}")
                issues += 1
                continue
                
            # Check 2: Is the symlink broken? (Points to a deleted file)
            if not symlink_path.resolve().exists():
                print(f"  {C_RED}✖ Broken symlink (Executable was deleted){C_RESET}")
                issues += 1
                continue

            print(f"  {C_GREEN}✔ Healthy{C_RESET}")

    print("\n--- Summary ---")
    if issues == 0:
        print(f"{C_GREEN}All systems go! No issues found.{C_RESET}")
    else:
        print(f"{C_RED}Found {issues} issue(s).{C_RESET} Try reinstalling the affected apps.")

if __name__ == "__main__":
    main()
