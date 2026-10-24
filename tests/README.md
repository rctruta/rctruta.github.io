# Tests

    python3 -m unittest discover -s tests -t .

Standard library `unittest`, discovered from the repository root.

Run automatically by `./build` after the pages are generated, and by CI on every push and pull request.

## Test Suite Overview

| Test Module | Coverage |
| :--- | :--- |
| `test_pipeline.py` | Config and taxonomy schemas required by the build |
| `test_navigation.py` | Navigation integrity across all pages |
| `test_descriptions.py` | Data consistency with generated metadata |
| `test_contact.py` | Contact endpoints and form structure |
| `test_nothing_vanishes.py` | Ensures all data records reach generated pages |
| `test_bio.py` | Single source of truth for bio strings |
| `test_vocabulary_docs.py` | Controlled vocabulary consistency |
| `test_recognition.py` | Recognition metadata and attribution verification |
| `test_vocabulary_pages.py` | Scope notes and tag accessibility |

## Preconditions

Nothing here requires network access or external credentials. The suite runs identically in local environments and GitHub Actions CI.
