#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_RUNTIME_DIR = REPO_ROOT / "tmp" / "runtime" / "openclaw"
DEFAULT_SKILLS_SOURCE = Path.home() / "study" / "openclaw" / "agent-skills"

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

RUNTIME_COPY_RULES = [
    {"src": Path("openclaw.mjs")},
    {"src": Path("package.json")},
    {"src": Path("dist"), "filter": "dist"},
    {"src": Path("node_modules"), "filter": "node_modules"},
    {
        "src": Path("docs") / "reference" / "templates",
        "dest": Path("docs") / "reference" / "templates",
    },
    {"src": Path("extensions"), "optional": True},
    {"src": Path("skills"), "optional": True},
    {"src": Path("assets"), "optional": True},
]


def run_command(args, cwd=REPO_ROOT, capture_output=False, env=None):
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        if capture_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        print(f"✗ Command failed: {' '.join(args)}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def remove_extensions(extension_ids):
    extensions_root = REPO_ROOT / "extensions"
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
    ui_dir = REPO_ROOT / "ui"
    if not ui_dir.exists():
        print("⚠ UI folder not found: ui")
        return False

    shutil.rmtree(ui_dir)
    print("✓ Deleted ui folder: ui")
    return True


def remove_node_modules():
    node_modules_dir = REPO_ROOT / "node_modules"
    if not node_modules_dir.exists():
        print("⚠ node_modules not found: node_modules")
        return False

    shutil.rmtree(node_modules_dir)
    print("✓ Deleted node_modules folder: node_modules")
    return True


def run_pnpm_install():
    print("\n📦 Running pnpm install...")
    run_command(["pnpm", "install"], capture_output=True)
    print("✓ pnpm install completed")


def run_pnpm_build():
    print("\n📦 Running pnpm build...")
    run_command(["pnpm", "build"], capture_output=True)
    print("✓ pnpm build completed")


def update_package_json_name(new_name):
    package_file = REPO_ROOT / "package.json"

    if not package_file.exists():
        print("Error: package.json not found", file=sys.stderr)
        sys.exit(1)

    content = package_file.read_text(encoding="utf-8")
    content = re.sub(
        r'("name"\s*:\s*)"[^"]*"',
        rf'\1"{new_name}"',
        content,
    )
    content = re.sub(
        r'("prepack"\s*:\s*)"[^"]*"',
        r'\1"pnpm build"',
        content,
    )
    package_file.write_text(content, encoding="utf-8")

    print(f"✓ Updated name to: {new_name}")
    print("✓ Updated prepack to: pnpm build")


def sync_skills(source_skills=DEFAULT_SKILLS_SOURCE):
    skills_dir = REPO_ROOT / "skills"
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
        print("✓ Deleted current skills folder")

    if source_skills.exists():
        shutil.copytree(source_skills, skills_dir)
        print(f"✓ Copied skills from {source_skills}")
    else:
        print(f"⚠ Warning: {source_skills} not found")


def should_skip_common_path(relative_path):
    rel = relative_path.replace("\\", "/")
    return (
        rel == ".DS_Store"
        or rel.endswith("/.DS_Store")
        or rel == ".git"
        or rel.startswith(".git/")
        or "/.git/" in rel
    )


def should_skip_dist_path(relative_path):
    rel = relative_path.replace("\\", "/")
    return (
        should_skip_common_path(rel)
        or rel.endswith(".map")
        or rel.endswith(".d.ts")
        or rel.endswith(".d.mts")
        or rel.endswith(".d.cts")
    )


def should_skip_node_modules_path(relative_path):
    rel = relative_path.replace("\\", "/")
    return (
        rel == ".modules.yaml"
        or rel == ".pnpm-workspace-state-v1.json"
        or rel == ".pnpm"
        or rel.startswith(".pnpm/")
        or "/.pnpm/" in rel
        or should_skip_common_path(rel)
    )


def should_skip_path(relative_path, filter_name=None):
    if filter_name == "dist":
        return should_skip_dist_path(relative_path)
    if filter_name == "node_modules":
        return should_skip_node_modules_path(relative_path)
    return should_skip_common_path(relative_path)


def build_copytree_ignore(src_dir, filter_name):
    src_dir = Path(src_dir)

    def ignore(current_dir, names):
        current_path = Path(current_dir)
        rel_dir = Path(".") if current_path == src_dir else current_path.relative_to(src_dir)
        ignored = []
        for name in names:
            rel_path = name if rel_dir == Path(".") else (rel_dir / name).as_posix()
            if should_skip_path(rel_path, filter_name):
                ignored.append(name)
        return ignored

    return ignore


def get_runtime_top_level_node_modules_allowlist():
    package_file = REPO_ROOT / "package.json"
    package_data = json.loads(package_file.read_text(encoding="utf-8"))
    allowlist = {".bin"}

    for section_name in ("dependencies", "peerDependencies"):
        section = package_data.get(section_name) or {}
        for package_name in section.keys():
            if package_name.startswith("@"):
                allowlist.add(package_name.split("/", 1)[0])
            else:
                allowlist.add(package_name)

    return allowlist


def prune_top_level_node_modules(dest_dir):
    allowlist = get_runtime_top_level_node_modules_allowlist()
    for entry in dest_dir.iterdir():
        if entry.name in allowlist:
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def copy_node_modules(src_dir, dest_dir):
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "rsync",
            "-aL",
            "--exclude",
            ".pnpm/",
            "--exclude",
            ".modules.yaml",
            "--exclude",
            ".pnpm-workspace-state-v1.json",
            "--exclude",
            ".DS_Store",
            "--exclude",
            ".git/",
            f"{src_dir}/",
            str(dest_dir),
        ],
        capture_output=True,
    )
    prune_top_level_node_modules(dest_dir)


def copy_directory(src_dir, dest_dir, filter_name=None):
    if filter_name == "node_modules":
        copy_node_modules(src_dir, dest_dir)
        return

    for root, dirnames, filenames in os.walk(src_dir, followlinks=False):
        root_path = Path(root)
        rel_root = Path(".") if root_path == src_dir else root_path.relative_to(src_dir)
        current_dest = dest_dir if rel_root == Path(".") else dest_dir / rel_root
        current_dest.mkdir(parents=True, exist_ok=True)

        kept_dirs = []
        for dirname in dirnames:
            rel_path = dirname if rel_root == Path(".") else (rel_root / dirname).as_posix()
            if should_skip_path(rel_path, filter_name):
                continue
            dir_path = root_path / dirname
            if dir_path.is_symlink():
                target = dir_path.resolve(strict=False)
                if not target.exists():
                    print(f"⚠ Skipped broken symlink directory: {dir_path} -> {target}")
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            rel_path = filename if rel_root == Path(".") else (rel_root / filename).as_posix()
            if should_skip_path(rel_path, filter_name):
                continue
            src_file = root_path / filename
            if src_file.is_symlink():
                target = src_file.resolve(strict=False)
                if not target.exists():
                    print(f"⚠ Skipped broken symlink file: {src_file} -> {target}")
                    continue
                if target.is_dir():
                    print(f"⚠ Skipped symlink-to-directory file entry: {src_file} -> {target}")
                    continue
                src_file = target
            dest_file = dest_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)


def copy_runtime_bundle(output_dir):
    output_dir = output_dir.resolve()
    staging_dir = output_dir.parent / f".{output_dir.name}.tmp"

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Building OpenClaw runtime directory: {output_dir}")
    run_command(
        ["pnpm", "--filter", ".", "deploy", "--legacy", "--prod", str(staging_dir)],
        capture_output=True,
    )

    runtime_env = os.environ.copy()
    runtime_env["NODE_DISABLE_COMPILE_CACHE"] = "1"

    print("\n🔎 Verifying runtime CLI...")
    run_command(
        ["node", "openclaw.mjs", "--help"],
        cwd=staging_dir,
        capture_output=True,
        env=runtime_env,
    )
    print("✓ Runtime check passed: openclaw --help")
    run_command(
        ["node", "openclaw.mjs", "gateway", "--help"],
        cwd=staging_dir,
        capture_output=True,
        env=runtime_env,
    )
    print("✓ Runtime check passed: openclaw gateway --help")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(staging_dir), str(output_dir))
    print(f"✓ Runtime directory ready: {output_dir}")
    return output_dir


def run_publish():
    print("\n📤 Running npm publish...")
    auth_token = "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"
    result = subprocess.run(
        ["npm", "publish", f"--//registry.npmjs.org/:_authToken={auth_token}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"✗ npm publish failed:\n{result.stderr}")
        sys.exit(1)
    print("✓ npm publish completed")
    print(result.stdout)


def run_slim_pipeline(new_name=None):
    print("\n🧹 Removing node_modules...")
    remove_node_modules()

    run_pnpm_install()
    run_pnpm_build()
    if new_name:
        update_package_json_name(new_name)

    print("\n🧹 Removing extensions...")
    deleted, missing = remove_extensions(EXTENSIONS)
    print(f"✓ Extensions processed: {len(deleted)}")
    if missing:
        print(f"⚠ Not found: {', '.join(missing)}")

    print("\n🧹 Removing ui...")
    remove_ui()

    print("\n🧹 Syncing skills...")
    sync_skills()


def run_slim_and_publish(new_name, runtime_dir=DEFAULT_RUNTIME_DIR):
    run_slim_pipeline(new_name)
    copy_runtime_bundle(runtime_dir)
    run_publish()


def run_slim_and_build_runtime(runtime_dir=DEFAULT_RUNTIME_DIR):
    run_slim_pipeline()
    copy_runtime_bundle(runtime_dir)


def print_usage():
    print("Usage:")
    print("  python update_package.py <new-name> [runtime-output-dir]")
    print("  python update_package.py build-runtime [output-dir]")
    print("")
    print("Notes:")
    print("  - Both commands run the slimming flow first.")
    print("  - The publish command also exports runtime before npm publish.")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    if sys.argv[1] in {"-h", "--help"}:
        print_usage()
        sys.exit(0)

    if sys.argv[1] == "build-runtime":
        output_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_RUNTIME_DIR
        run_slim_and_build_runtime(output_dir)
        sys.exit(0)

    new_name = sys.argv[1]
    runtime_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_RUNTIME_DIR
    run_slim_and_publish(new_name, runtime_dir)


if __name__ == "__main__":
    main()
