"""Build the static search index and put the search box on every page.

    python3 tools/build_search.py

Pagefind builds the index at publish time and the search runs entirely in the
reader's browser — no server, no query logging, nothing to keep running. Re-run
it after any content change, or the index describes the previous version of the
site.

Requires node. The index lands in pagefind/ and is committed, because GitHub
Pages serves files rather than building them.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = [
    "index.html", "work.html", "teaching.html", "speaking.html",
    "writing.html", "tags.html", "contact.html",
]

SNIPPET = """<div class="searchbox"><div class="wrap"><div id="search"></div></div></div>
<link href="pagefind/pagefind-ui.css" rel="stylesheet">
<script src="pagefind/pagefind-ui.js"></script>
<script>
  window.addEventListener('DOMContentLoaded', () => {
    new PagefindUI({
      element: '#search',
      showSubResults: true,
      showImages: false,
      pageSize: 8,
      translations: { placeholder: 'Search this site', zero_results: 'Nothing for [SEARCH_TERM]' }
    });
  });
</script>"""

run = subprocess.run(
    ["npx", "-y", "pagefind", "--site", ".", "--glob", "*.html"],
    cwd=ROOT, capture_output=True, text=True,
)
if run.returncode != 0:
    sys.exit("pagefind failed:\n" + run.stderr[-2000:])
print(re.sub(r"\n+", " ", re.search(r"Total:.*?sorts", run.stdout, re.S).group(0)))

placed = 0
for name in PAGES:
    page = ROOT / name
    if not page.exists():
        continue
    text = page.read_text()
    text = re.sub(
        r'<div class="searchbox">.*?</script>\n?', "", text, flags=re.S
    )  # idempotent
    text = text.replace("</body>", SNIPPET + "\n</body>", 1)
    page.write_text(text)
    placed += 1

print(f"search box placed on {placed} pages")
