#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python tools/validate_site.py --sources-only
fi
exec "${PYTHON:-python3}" tools/validate_site.py --sources-only
