#!/usr/bin/env python3
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_RUNTIME_DIR = REPO_ROOT / "tmp" / "runtime" / "openclaw"
DEFAULT_RUNTIME_ARCHIVE_ROOT = REPO_ROOT / "tmp" / "runtime-archives"
DEFAULT_SKILLS_SOURCE = Path.home() / "study" / "openclaw" / "agent-skills"
FIXED_OPENCLAW_RUNTIME_OSS_PREFIX = "assets/openclaw-runtime"

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


def first_non_empty(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def trim_slash(value):
    if not value:
        return ""
    return value.strip().strip("/")


def join_oss_key(*parts):
    return "/".join(trim_slash(part) for part in parts if trim_slash(part))


def normalize_bucket_name(bucket):
    if not bucket:
        return None
    normalized = bucket.strip()
    if normalized.startswith("oss://"):
        normalized = normalized[6:]
    return trim_slash(normalized)


def parse_simple_ini(content):
    data = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";") or line.startswith("["):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key and value:
            data[key] = value
    return data


def load_ossutil_config():
    config_path = Path.home() / ".ossutilconfig"
    if not config_path.exists():
        return {}
    try:
        return parse_simple_ini(config_path.read_text(encoding="utf-8"))
    except OSError as err:
        print(f"⚠ Failed to read {config_path}: {err}", file=sys.stderr)
        return {}

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

    last_error = None
    for attempt in range(5):
        try:
            shutil.rmtree(node_modules_dir)
            break
        except FileNotFoundError:
            break
        except OSError as err:
            last_error = err
            if err.errno != 66 or attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))
    else:
        if last_error is not None:
            raise last_error

    print("✓ Deleted node_modules folder: node_modules")
    return True


def sanitized_install_env():
    env = os.environ.copy()
    for key in list(env.keys()):
        if key.lower().startswith("npm_config_"):
            del env[key]
    env.pop("NODE_ENV", None)
    return env


def run_pnpm_install():
    print("\n📦 Running pnpm install...")
    run_command(
        ["pnpm", "install", "--prod=false"],
        capture_output=True,
        env=sanitized_install_env(),
    )
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


def prune_bin_directories(root_dir):
    removed = 0
    for current_root, dirnames, _ in os.walk(root_dir, topdown=True):
        kept_dirnames = []
        for dirname in dirnames:
            if dirname != ".bin":
                kept_dirnames.append(dirname)
                continue
            shutil.rmtree(Path(current_root) / dirname)
            removed += 1
        dirnames[:] = kept_dirnames
    if removed:
        print(f"✓ Removed {removed} node_modules/.bin directories")


def count_symlinks(root_dir):
    if not root_dir.exists():
        return 0

    count = 0
    for path in root_dir.rglob("*"):
        if path.is_symlink():
            count += 1
    return count


def detect_runtime_target():
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        arch = "aarch64" if machine == "arm64" else "x86_64"
        return f"{arch}-apple-darwin"
    if system == "Linux":
        arch = "aarch64" if machine in {"aarch64", "arm64"} else "x86_64"
        return f"{arch}-unknown-linux-gnu"
    if system == "Windows":
        return "x86_64-pc-windows-msvc"

    print(f"✗ Unsupported runtime platform: {system}/{machine}", file=sys.stderr)
    sys.exit(1)


def compute_sha256(file_path):
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_runtime_archive(runtime_dir, target_triple, archive_root=DEFAULT_RUNTIME_ARCHIVE_ROOT):
    archive_dir = archive_root / target_triple
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / "openclaw-runtime.tar.gz"
    sha_path = archive_dir / "openclaw-runtime.tar.gz.sha256"

    print(f"\n📦 Creating runtime archive: {archive_path}")
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(runtime_dir, arcname="openclaw")

    sha256 = compute_sha256(archive_path)
    sha_path.write_text(f"{sha256}\n", encoding="utf-8")
    print(f"✓ Runtime archive ready: {archive_path}")
    print(f"✓ Runtime archive SHA256: {sha256}")
    return archive_path, sha_path, sha256


def resolve_runtime_oss_settings():
    config = load_ossutil_config()
    bucket = normalize_bucket_name(
        first_non_empty(os.environ.get("OSS_BUCKET"), config.get("bucket"), "totou")
    )
    return {
        "bucket": bucket,
        "runtime_prefix": FIXED_OPENCLAW_RUNTIME_OSS_PREFIX,
        "config_path": Path.home() / ".ossutilconfig",
    }


def build_runtime_oss_keys(target_triple, runtime_prefix):
    runtime_root = join_oss_key(runtime_prefix, target_triple)
    archive_key = join_oss_key(runtime_root, "openclaw-runtime.tar.gz")
    sha_key = join_oss_key(runtime_root, "openclaw-runtime.tar.gz.sha256")
    return archive_key, sha_key


def upload_runtime_archive(archive_path, sha_path, target_triple):
    settings = resolve_runtime_oss_settings()
    ossutil_path = shutil.which("ossutil")
    if not ossutil_path:
        print("✗ ossutil not found in PATH", file=sys.stderr)
        sys.exit(1)
    if not settings["config_path"].exists():
        print(f"✗ ossutil config not found: {settings['config_path']}", file=sys.stderr)
        sys.exit(1)

    archive_key, sha_key = build_runtime_oss_keys(target_triple, settings["runtime_prefix"])
    archive_target = f"oss://{settings['bucket']}/{archive_key}"
    sha_target = f"oss://{settings['bucket']}/{sha_key}"

    print("\n📤 Uploading runtime archive to OSS...")
    print(f"  {archive_path} -> {archive_target}")
    run_command(["ossutil", "cp", "-f", str(archive_path), archive_target], capture_output=True)
    print(f"  {sha_path} -> {sha_target}")
    run_command(["ossutil", "cp", "-f", str(sha_path), sha_target], capture_output=True)
    print("✓ Runtime archive uploaded to OSS")


def package_runtime_artifacts(runtime_dir, upload_oss=False):
    target_triple = detect_runtime_target()
    archive_path, sha_path, _ = create_runtime_archive(runtime_dir, target_triple)
    if upload_oss:
        upload_runtime_archive(archive_path, sha_path, target_triple)


def copy_runtime_bundle(output_dir):
    output_dir = output_dir.resolve()
    staging_dir = output_dir.parent / f".{output_dir.name}.tmp"

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Building OpenClaw runtime directory: {output_dir}")
    run_command(
        [
            "pnpm",
            "--filter",
            ".",
            "deploy",
            "--legacy",
            "--prod",
            "--config.node-linker=hoisted",
            "--config.package-import-method=copy",
            str(staging_dir),
        ],
        capture_output=True,
    )

    print("\n🧹 Removing node_modules/.bin symlink directories...")
    prune_bin_directories(staging_dir)

    symlink_count = count_symlinks(staging_dir)
    if symlink_count != 0:
        print(
            f"✗ Runtime directory still contains symlinks after deploy: {symlink_count}",
            file=sys.stderr,
        )
        sys.exit(1)

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


def run_slim_and_publish(new_name, runtime_dir=DEFAULT_RUNTIME_DIR, upload_oss=False):
    run_slim_pipeline(new_name)
    runtime_dir = copy_runtime_bundle(runtime_dir)
    package_runtime_artifacts(runtime_dir, upload_oss=upload_oss)
    run_publish()


def run_slim_and_build_runtime(runtime_dir=DEFAULT_RUNTIME_DIR, upload_oss=False):
    run_slim_pipeline()
    runtime_dir = copy_runtime_bundle(runtime_dir)
    package_runtime_artifacts(runtime_dir, upload_oss=upload_oss)


def print_usage():
    print("Usage:")
    print("  python update_package.py <new-name> [runtime-output-dir] [--upload-oss]")
    print("  python update_package.py build-runtime [output-dir] [--upload-oss]")
    print("")
    print("Notes:")
    print("  - Both commands run the slimming flow first.")
    print("  - Both commands also produce tmp/runtime-archives/<target>/openclaw-runtime.tar.gz")
    print("  - Use --upload-oss to upload the runtime archive and .sha256 via ossutil.")
    print(f"  - Runtime archives are uploaded to oss://<bucket>/{FIXED_OPENCLAW_RUNTIME_OSS_PREFIX}/<target>/")


def parse_cli_args(argv):
    upload_oss = False
    positionals = []

    index = 1
    while index < len(argv):
        arg = argv[index]
        if arg == "--upload-oss":
            upload_oss = True
        else:
            positionals.append(arg)
        index += 1

    return {
        "positionals": positionals,
        "upload_oss": upload_oss,
    }


def main():
    parsed = parse_cli_args(sys.argv)
    positionals = parsed["positionals"]

    if len(positionals) < 1:
        print_usage()
        sys.exit(1)

    if positionals[0] in {"-h", "--help"}:
        print_usage()
        sys.exit(0)

    if positionals[0] == "build-runtime":
        output_dir = Path(positionals[1]) if len(positionals) >= 2 else DEFAULT_RUNTIME_DIR
        run_slim_and_build_runtime(
            output_dir,
            upload_oss=parsed["upload_oss"],
        )
        sys.exit(0)

    new_name = positionals[0]
    runtime_dir = Path(positionals[1]) if len(positionals) >= 2 else DEFAULT_RUNTIME_DIR
    run_slim_and_publish(
        new_name,
        runtime_dir,
        upload_oss=parsed["upload_oss"],
    )


if __name__ == "__main__":
    main()
