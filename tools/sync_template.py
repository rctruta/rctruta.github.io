"""Propagate architectural, build script, and design system updates from rctruta.github.io to static-site-template.

    python3 tools/sync_template.py
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = ROOT.parent / "static-site-template"

if not TEMPLATE_ROOT.exists():
    sys.exit(f"Template directory not found at {TEMPLATE_ROOT}")

print("🔄 Syncing architecture and tools to static-site-template...")

# Files to sync
FILES_TO_SYNC = [
    "style.css",
    "data/TAXONOMY.md",
    "tools/config_loader.py",
    "tools/build_nav.py",
    "tools/build_tags.py",
    "tools/build_writing.py",
    "tools/build_speaking.mjs",
    "tools/build_search.py",
    "tools/check_private.py",
    "tools/test_tools.py",
]

for rel_path in FILES_TO_SYNC:
    src = ROOT / rel_path
    dest = TEMPLATE_ROOT / rel_path
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  ✓ Copied {rel_path}")

# Run build script inside template repository
print("\n🧪 Running ./build inside static-site-template...")
run = subprocess.run(["./build"], cwd=TEMPLATE_ROOT, capture_output=True, text=True)

if run.returncode == 0:
    print("✅ Template build passed successfully!")
else:
    print("❌ Template build failed:\n" + run.stderr)
    sys.exit(1)
