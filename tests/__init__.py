"""The site's test suite.

Moved out of tools/ on 2026-10-23. tools/ is for the builders -- one per
page -- and a test file sitting among them is why this looked like a project
without tests.

Stdlib unittest, discovered from the repository root:

    python3 -m unittest discover -s tests -t .

No pytest: the builders are stdlib plus pydantic and jinja2, and a test
runner that needs installing is one more thing between a clean checkout and
a green suite.

The site's modules live in tools/, so the package puts that on the path once
here rather than in every test file.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
