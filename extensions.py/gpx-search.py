#!/usr/bin/env python3
"""
gpx-search: Search GitHub for tools directly from the CLI.
"""
import sys
import json
import urllib.request
from urllib.error import URLError

C_BLUE = "\033[94m"
C_YELLOW = "\033[93m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"

def main():
    if len(sys.argv) < 2:
        print(f"Usage: gpx search <keyword>")
        sys.exit(1)

    query = "+".join(sys.argv[1:])
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5"
    
    print(f"{C_DIM}Searching GitHub for '{query}'...{C_RESET}\n")
    
    try:
        # Create a request with a User-Agent (GitHub requires this)
        req = urllib.request.Request(url, headers={'User-Agent': 'gpx-search-extension'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
            if data['total_count'] == 0:
                print(f"{C_YELLOW}No repositories found.{C_RESET}")
                return

            for repo in data['items']:
                name = repo['full_name']
                desc = repo['description'] or "No description provided."
                stars = repo['stargazers_count']
                
                print(f"{C_BLUE}{name}{C_RESET} {C_YELLOW}★ {stars}{C_RESET}")
                print(f"  {desc}")
                print(f"  {C_DIM}Install: gpx install {name}{C_RESET}\n")

    except URLError as e:
        print(f"Failed to connect to GitHub: {e}")

if __name__ == "__main__":
    main()
