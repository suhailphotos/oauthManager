"""
oauthManager CLI
================
Run:

    oauthmanager init          # after package install
"""

from __future__ import annotations
from pathlib import Path
import json
import platform
import shutil
import subprocess
import sys
import textwrap

import click

# --------------------------------------------------------------------------- #
# paths                                                                       #
# --------------------------------------------------------------------------- #
PKG_ROOT   = Path(__file__).resolve().parent
CONFIG_SRC = PKG_ROOT / ".config"                    # ship-with templates
CONFIG_DIR = Path.home() / ".oauthmanager"           # user home dir

TEMPLATE_FILES = [
    ("env.example",       ".env",              False),
    ("creds_config.json", "creds_config.json", False),
    ("creds_config.md",   "creds_config.md",   False),
]

# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #
def op_cli_installed() -> bool:
    return shutil.which("op") is not None


def op_cli_suggestion() -> str:
    sys_ = platform.system()
    if sys_ == "Darwin":   # macOS
        return "brew install 1password-cli"
    if sys_ == "Windows":
        return "winget install 1password-cli"
    if sys_ == "Linux":
        distro_hint = {
            "debian": "apt (Debian/Ubuntu)",
            "ubuntu": "apt (Ubuntu)",
            "fedora": "dnf",
            "centos": "yum",
            "alpine": "apk",
            "nixos":  "nix-env"
        }
        # very rough distro guess from /etc/os-release
        os_rel = Path("/etc/os-release")
        if os_rel.exists():
            for line in os_rel.read_text().splitlines():
                if line.startswith("ID="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                    return f"see docs • recommended manager: {distro_hint.get(distro,'apt')}"
        return "see docs • package managers: apt, dnf, yum, apk, nix"
    return "see docs"


def copy_templates() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    for src_name, dest_name, overwrite in TEMPLATE_FILES:
        src  = CONFIG_SRC / src_name
        dest = CONFIG_DIR / dest_name

        if not src.exists():
            click.secho(f"Template missing in package: {src}", fg="red")
            continue

        if dest.exists() and not overwrite:
            click.echo(f"· {dest.name} already exists – skipping")
            continue

        shutil.copy2(src, dest)
        click.echo(f"· Copied {dest.name}")


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
@click.group(help="oauthManager command-line interface")
def main() -> None:  # pragma: no cover
    pass


@main.command("init", help="Create ~/.oauthmanager and copy template files")
def cli_init() -> None:
    """Initialise local configuration directory and verify 1Password CLI."""
    click.secho("Initialising oauthManager", fg="cyan")

    # 1. copy template files
    copy_templates()

    # 2. ensure encryption key exists (constructor handles it)
    from oauthmanager.vaults.onepassword import OnePasswordVault
    OnePasswordVault()
    click.echo("· Encryption key ready")

    # 3. op CLI check
    if op_cli_installed():
        try:
            v = subprocess.check_output(["op", "--version"], text=True).strip()
            click.echo(f"· 1Password CLI detected (v{v})")
        except Exception:
            click.echo("· 1Password CLI detected")
    else:
        click.secho("\n⚠  1Password CLI ('op') not found on PATH", fg="yellow")
        click.echo(f"  install via: {op_cli_suggestion()}")
        click.echo("  full instructions: https://developer.1password.com/docs/cli/get-started")

    click.secho("\nDone.", fg="green")


if __name__ == "__main__":  # pragma: no cover
    main()
