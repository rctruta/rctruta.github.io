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

SNIPPET = """<!-- search:start -->
<div class="searchmodal" id="searchmodal" hidden data-pagefind-ignore>
  <div class="searchmodal__panel" role="dialog" aria-modal="true" aria-label="Search this site">
    <button type="button" class="searchmodal__close" aria-label="Close search" data-search-close>&times;</button>
    <div id="search"></div>
  </div>
</div>
<link href="pagefind/pagefind-ui.css" rel="stylesheet">
<script src="pagefind/pagefind-ui.js"></script>
<script>
(() => {
  const modal = document.getElementById('searchmodal');
  let ui = null;

  const open = () => {
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    if (!ui) {
      ui = new PagefindUI({
        element: '#search',
        showSubResults: true,
        showImages: false,
        pageSize: 8,
        highlightParam: "highlight",
        translations: {
          placeholder: 'Search this site',
          zero_results: 'Nothing found for [SEARCH_TERM]'
        }
      });
    }
    const saved = sessionStorage.getItem('pagefind_query');
    const input = modal.querySelector('input');
    if (input) {
      if (saved && !input.value) {
        ui.triggerSearch(saved);
      }
      input.focus();
    }
  };

  const close = () => {
    modal.hidden = true;
    document.body.style.overflow = '';
  };

  document.querySelectorAll('[data-search-open]').forEach(b => b.addEventListener('click', open));
  document.querySelectorAll('[data-search-close]').forEach(b => b.addEventListener('click', close));

  modal.addEventListener('input', e => {
    if (e.target && e.target.tagName === 'INPUT') {
      sessionStorage.setItem('pagefind_query', e.target.value);
    }
  });

  modal.addEventListener('click', e => {
    if (e.target === modal) close();
    const link = e.target.closest('a');
    if (link && link.getAttribute('href')) {
      close();
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !modal.hidden) close();
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); modal.hidden ? open() : close(); }
  });
})();
</script>
<!-- search:end -->"""

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
    # strip any previous block wholesale — the snippet contains two </script>
    # tags, so a non-greedy match to the first one leaves debris behind and the
    # next run stacks a second search UI on top of it
    text = re.sub(r'<!-- search:start -->.*?<!-- search:end -->\n?', "", text, flags=re.S)
    text = re.sub(r'<div class="search(?:box|modal)".*?</script>\n?', "", text, flags=re.S)
    text = re.sub(r'<link href="pagefind/.*?</script>\n?', "", text, flags=re.S)
    text = text.replace("</body>", SNIPPET + "\n</body>", 1)
    page.write_text(text)
    placed += 1

print(f"search box placed on {placed} pages")
