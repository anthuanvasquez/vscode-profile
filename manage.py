#!/usr/bin/env python3
"""
VS Code Profile Manager
Manages modular configurations and extensions for VS Code profiles without duplication.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
EXTENSIONS_DIR = ROOT_DIR / "extensions"
SETTINGS_FILE = ROOT_DIR / "settings.json"
KEYBINDINGS_FILE = ROOT_DIR / "keybindings.json"

PROFILES = {
    "Default": "default.txt",
    "Audio": "audio.txt",
    "Game": "game.txt",
    "iOS": "ios.txt",
}

# Standard VS Code User directory on macOS
VSCODE_USER_DIR = Path.home() / "Library/Application Support/Code/User"


def load_extensions(profile_file: str) -> list[str]:
    """Loads extensions by combining base.txt with the profile-specific file."""
    extensions = set()

    base_path = EXTENSIONS_DIR / "base.txt"
    if base_path.exists():
        with open(base_path, encoding="utf-8") as f:
            extensions.update(
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            )

    specific_path = EXTENSIONS_DIR / profile_file
    if specific_path.exists():
        with open(specific_path, encoding="utf-8") as f:
            extensions.update(
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            )

    return sorted(extensions)


def build_profiles():
    """Generates clean .code-profile files from settings.json and extension manifests."""
    if not SETTINGS_FILE.exists():
        print(f"Error: {SETTINGS_FILE} not found")
        sys.exit(1)

    with open(SETTINGS_FILE, encoding="utf-8") as f:
        settings_content = f.read()

    keybindings_content = "[]"
    if KEYBINDINGS_FILE.exists():
        with open(KEYBINDINGS_FILE, encoding="utf-8") as f:
            keybindings_content = f.read()

    print("🔨 Building clean .code-profile files...")

    for profile_name, ext_file in PROFILES.items():
        ext_list = load_extensions(ext_file)

        profile_data = {
            "name": profile_name,
            "settings": json.dumps({"settings": settings_content}),
            "keybindings": json.dumps(
                {"keybindings": keybindings_content, "platform": 1}
            ),
            "extensions": json.dumps(
                [{"identifier": {"id": ext_id}} for ext_id in ext_list]
            ),
        }

        output_path = ROOT_DIR / f"{profile_name}.code-profile"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False)

        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ {output_path.name:22} ({len(ext_list)} extensions, {size_kb:.1f} KB)")

    print("✨ Done! Profiles generated without globalState bloat.")


def sync_settings():
    """Syncs settings.json and keybindings.json directly to local VS Code profile directories."""
    if not VSCODE_USER_DIR.exists():
        print(f"VS Code user directory not found at {VSCODE_USER_DIR}")
        return

    # Sync to Default profile (root User)
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings_data = f.read()

    target_default_settings = VSCODE_USER_DIR / "settings.json"
    with open(target_default_settings, "w", encoding="utf-8") as f:
        f.write(settings_data)
    print(f"  ✓ Synced to Default: {target_default_settings}")

    if KEYBINDINGS_FILE.exists():
        with open(KEYBINDINGS_FILE, "r", encoding="utf-8") as f:
            keybindings_data = f.read()
        target_default_keybindings = VSCODE_USER_DIR / "keybindings.json"
        with open(target_default_keybindings, "w", encoding="utf-8") as f:
            f.write(keybindings_data)

    # Search for secondary profiles in storage.json
    storage_file = VSCODE_USER_DIR / "globalStorage" / "storage.json"
    if not storage_file.exists():
        return

    try:
        with open(storage_file, encoding="utf-8") as f:
            storage_data = json.load(f)
    except Exception as e:
        print(f"Could not read storage.json: {e}")
        return

    profiles = storage_data.get("userDataProfiles", [])
    profiles_dir = VSCODE_USER_DIR / "profiles"

    print("🔄 Syncing settings to local VS Code profiles...")
    for prof in profiles:
        name = prof.get("name")
        location = prof.get("location")
        if not name or not location:
            continue

        target_dir = profiles_dir / location
        if target_dir.exists():
            target_settings = target_dir / "settings.json"
            with open(target_settings, "w", encoding="utf-8") as f:
                f.write(settings_data)

            if KEYBINDINGS_FILE.exists():
                target_keys = target_dir / "keybindings.json"
                with open(target_keys, "w", encoding="utf-8") as f:
                    f.write(keybindings_data)

            print(f"  ✓ Synced to profile '{name}' ({location})")


def install_extensions(target_profile: str | None = None):
    """Installs extensions in VS Code using the 'code' CLI."""
    targets = {target_profile: PROFILES[target_profile]} if target_profile else PROFILES

    for profile_name, ext_file in targets.items():
        ext_list = load_extensions(ext_file)
        print(f"\n📦 Installing {len(ext_list)} extensions into profile '{profile_name}'...")

        for ext_id in ext_list:
            cmd = ["code"]
            if profile_name != "Default":
                cmd.extend(["--profile", profile_name])
            cmd.extend(["--install-extension", ext_id])

            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"  ✓ {ext_id}")
            else:
                print(f"  ✗ {ext_id}: {res.stderr.strip() or res.stdout.strip()}")


def main():
    parser = argparse.ArgumentParser(description="VS Code Profile Manager")
    parser.add_argument(
        "--build", action="store_true", help="Build clean .code-profile files"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sync settings.json and keybindings.json to local VS Code profiles",
    )
    parser.add_argument(
        "--install",
        nargs="?",
        const="ALL",
        metavar="PROFILE",
        help="Install extensions via CLI (e.g. --install Audio or --install)",
    )

    args = parser.parse_args()

    # Default to build if no arguments provided
    if not (args.build or args.sync or args.install):
        build_profiles()
        return

    if args.build:
        build_profiles()

    if args.sync:
        sync_settings()

    if args.install:
        prof = None if args.install == "ALL" else args.install
        if prof and prof not in PROFILES:
            print(f"Invalid profile '{prof}'. Available options: {list(PROFILES.keys())}")
            sys.exit(1)
        install_extensions(prof)


if __name__ == "__main__":
    main()
