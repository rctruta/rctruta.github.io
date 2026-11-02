#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ -x .venv/bin/python ]; then
  PYTHON=.venv/bin/python
else
  PYTHON="${PYTHON:-python3}"
fi
"$PYTHON" -m datamodel_code_generator --check
exec "$PYTHON" tools/validate_site.py --sources-only
