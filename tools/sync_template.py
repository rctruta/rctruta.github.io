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
# Architecture only. Data and generated pages are deliberately absent: syncing
# them republishes this site's content into the template, so every clone would start
# with her appearances, articles and teaching page and have to delete them. The
# template carries its own example data.
FILES_TO_SYNC = [
    # "build" is not synced: the template has no GitHub profile repo to write to

    "style.css",
    "templates/base.html",
    "templates/index.html",
    "templates/work.html",
    "templates/teaching.html",
    "templates/writing.html",
    "templates/speaking.html",
    "templates/contact.html",
    "templates/tags.html",
    "data/TAXONOMY.md",
    "tools/config_loader.py",
    "tools/model.py",
    "tools/page.py",
    "tools/bio.py",
    "tools/build_nav.py",
    "tools/build_tags.py",
    "tools/build_work.py",
    "tools/build_teaching.py",
    "tools/build_writing.py",
    "tools/build_contact.py",
    "tools/build_index.py",
    "tools/build_speaking.py",
    "tools/malloy_chart.py",
    "tools/build_search.py",
    "tools/check_private.py",
    "tools/test_tools.py",
]

for rel_path in FILES_TO_SYNC:
    src = ROOT / rel_path
    dest = TEMPLATE_ROOT / rel_path
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        if src.stat().st_mode & 0o111:
            dest.chmod(0o755)
        print(f"  ✓ Copied {rel_path}")

# Run build script inside template repository
print("\n🧪 Running ./build inside static-site-template...")
run = subprocess.run(["./build"], cwd=TEMPLATE_ROOT, capture_output=True, text=True)

if run.returncode == 0:
    print("✅ Template build passed successfully!")
else:
    print("❌ Template build failed:\n" + run.stderr)
    sys.exit(1)
