#!/usr/bin/env bash
# Usage: ops/scripts/export_pdf.sh <input.md> <output.pdf>
# Markdown -> (lint) -> styled HTML (resume.css + resume.lua) -> A4 PDF via headless Chromium.
# Refuses to export Markdown that breaks the house format; fix with
#   python3 ops/scripts/resume_md.py normalise <input.md>
# After exporting, run: python3 ops/scripts/check_pdf.py <output.pdf> <input.md>
set -euo pipefail
IN="$1"; OUT="$2"; DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/resume_md.py" lint "$IN"
TMP="$(mktemp --suffix=.html)"
pandoc "$IN" -f gfm -t html5 -s --metadata title=" " -M document-css=false --lua-filter "$DIR/resume.lua" \
  -H <(printf '<style>\n%s\n</style>\n' "$(cat "$DIR/resume.css")") -o "$TMP"
# Chromium: set CHROME to its path, or let the script look in the usual places.
if [ -z "${CHROME:-}" ]; then
  for c in /opt/pw-browsers/chromium-*/chrome-linux*/chrome \
           "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome \
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    [ -x "$c" ] && CHROME="$c" && break
  done
  [ -z "${CHROME:-}" ] && CHROME="$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)"
fi
if [ -z "${CHROME:-}" ]; then
  echo "export_pdf: no Chromium or Chrome found. Install one, or set CHROME to its path." >&2
  rm -f "$TMP"; exit 1
fi
mkdir -p "$(dirname "$OUT")"
"$CHROME" --headless --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf="$OUT" "file://$TMP" 2>/dev/null
rm -f "$TMP"
[ -s "$OUT" ] || { echo "export_pdf: Chromium ran but wrote no PDF at $OUT" >&2; exit 1; }
echo "wrote $OUT"
