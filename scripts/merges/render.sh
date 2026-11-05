#!/bin/sh
# Rebuild out/merges.csv, the HTML charts, and PNG copies of each chart.
# PNGs are screenshots taken with headless Google Chrome at 2x resolution.
set -e
cd "$(dirname "$0")"

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

mkdir -p out
python3 merges.py report > out/report.txt
echo "Wrote out/report.txt"
python3 plot.py

# name, window height (the width is the same for all)
for spec in merges-per-month:560 merges-per-month-line:560 merges-per-month-people:775; do
  name=${spec%%:*}
  height=${spec##*:}
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size=1140,"$height" --screenshot="out/$name.png" "file://$PWD/out/$name.html" 2>/dev/null
  echo "Wrote out/$name.png"
done
