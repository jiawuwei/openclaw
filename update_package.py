#!/usr/bin/env python3
import re
import sys
import shutil
import subprocess
from pathlib import Path

EXTENSIONS = [
    "bluebubbles",
    "discord",
    "feishu",
    "googlechat",
    "imessage",
    "irc",
    "line",
    "matrix",
    "mattermost",
    "msteams",
    "nextcloud-talk",
    "nostr",
    "signal",
    "slack",
    "synology-chat",
    "telegram",
    "tlon",
    "twitch",
    "whatsapp",
    "zalo",
    "zalouser",
    "phone-control",
    "qwen-portal-auth",
    "minimax-portal-auth",
    "google-gemini-cli-auth",
    "shared",
    "test-utils",
    "copilot-proxy",
]


def remove_extensions(extension_ids):
    extensions_root = Path("extensions")
    deleted = []
    missing = []

    for extension_id in extension_ids:
        target = extensions_root / extension_id
        if not target.exists():
            missing.append(extension_id)
            continue

        shutil.rmtree(target)
        print(f"✓ Deleted extension: {target}")
        deleted.append(extension_id)

    return deleted, missing


def remove_ui():
    ui_dir = Path("ui")
    if not ui_dir.exists():
        print("⚠ UI folder not found: ui")
        return False

    shutil.rmtree(ui_dir)
    print("✓ Deleted ui folder: ui")
    return True


def remove_node_modules():
    node_modules_dir = Path("node_modules")
    if not node_modules_dir.exists():
        print("⚠ node_modules not found: node_modules")
        return False

    shutil.rmtree(node_modules_dir)
    print("✓ Deleted node_modules folder: node_modules")
    return True


def run_pnpm_install():
    print("\n📦 Running pnpm install...")
    result = subprocess.run(["pnpm", "install"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"✗ pnpm install failed:\n{result.stderr}")
        sys.exit(1)
    print("✓ pnpm install completed")


def run_pnpm_build():
    print("\n📦 Running pnpm build...")
    result = subprocess.run(["pnpm", "build"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"✗ pnpm build failed:\n{result.stderr}")
        sys.exit(1)
    print("✓ pnpm build completed")


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_package.py <new-name>")
        sys.exit(1)

    new_name = sys.argv[1]
    package_file = Path("package.json")

    if not package_file.exists():
        print("Error: package.json not found")
        sys.exit(1)

    print("\n🧹 Removing node_modules...")
    remove_node_modules()

    run_pnpm_install()

    # Read package.json as text
    with open(package_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update name field
    content = re.sub(
        r'("name"\s*:\s*)"[^"]*"',
        rf'\1"{new_name}"',
        content
    )

    # Update prepack script
    content = re.sub(
        r'("prepack"\s*:\s*)"[^"]*"',
        r'\1"pnpm build"',
        content
    )

    # Write back
    with open(package_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Updated name to: {new_name}")
    print("✓ Updated prepack to: pnpm build")

    print("\n🧹 Removing extensions...")
    deleted, missing = remove_extensions(EXTENSIONS)
    print(f"✓ Extensions processed: {len(deleted)}")
    if missing:
        print(f"⚠ Not found: {', '.join(missing)}")

    print("\n🧹 Removing ui...")
    remove_ui()

    # Delete current skills folder
    skills_dir = Path("skills")
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
        print("✓ Deleted current skills folder")

    # Copy skills from ~/.openclaw/workspace/skills
    source_skills = Path.home() / "study" / "openclaw" / "agent-skills"
    if source_skills.exists():
        shutil.copytree(source_skills, skills_dir)
        print(f"✓ Copied skills from {source_skills}")
    else:
        print(f"⚠ Warning: {source_skills} not found")

    # Run npm publish
    print("\n📤 Running npm publish...")
    auth_token = "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"
    result = subprocess.run(
        ["npm", "publish", f"--//registry.npmjs.org/:_authToken={auth_token}"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"✗ npm publish failed:\n{result.stderr}")
        sys.exit(1)
    print("✓ npm publish completed")
    print(result.stdout)


if __name__ == '__main__':
    main()
