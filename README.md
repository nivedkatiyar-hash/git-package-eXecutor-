# 📦 gpx (Git Package eXecutor)

`gpx` is a lightweight, zero-dependency package manager that lets you instantly install and run GitHub repositories as global command-line tools. 

Think of it like `pipx` or `npm install -g`, but universally designed for any GitHub repository. It securely isolates your downloads into `~/.local/share/gpx` and links the executables to your PATH.

## ✨ Features

* **Zero Dependencies:** Written purely in Python's standard library. No need to run `pip install` before using it.
* **Global Access:** Automatically creates symlinks so you can run installed tools from anywhere in your terminal.
* **Auto-Discovery:** Automatically finds entry points like `run.sh`, `main.py`, or scripts matching the repo name.
* **Plugin Ecosystem:** Features a full extension system. Install third-party plugins to add brand new commands directly to `gpx`.
* **Built-in Scaffolding:** Generate ready-to-publish, `gpx`-compatible tools and extensions with a single command.

---

## 🚀 Installation

Because `gpx` is a system tool, you only need to "bootstrap" it once. 

Run these commands in your terminal to download it and set it up:

```bash
# 1. Download the script directly from this repository
curl -O [https://raw.githubusercontent.com/YOUR_USERNAME/gpx/main/gpx.py](https://raw.githubusercontent.com/YOUR_USERNAME/gpx/main/gpx.py)

# 2. Make it executable
chmod +x gpx.py

# 3. Move it to your local binaries folder
mkdir -p ~/.local/bin
mv gpx.py ~/.local/bin/gpx
