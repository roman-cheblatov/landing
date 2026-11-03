#!/usr/bin/env bash
# Mux test with original audio, run QA, build contact sheet and a lighter web copy.
set -euo pipefail
cd "$(dirname "$0")/../.."
source /root/vo-venv/bin/activate
mkdir -p out test
python src/engine/assemble.py work/test/test_video.mp4 out/test_0000-0698.mp4 --f0 0 --f1 698 \
       --sheet test/contact_sheet.png --report test/checks.json
python src/engine/temporal_check.py out/test_0000-0698.mp4 0 174 355 552 > test/temporal_check.json
cat test/temporal_check.json
ffmpeg -hide_banner -loglevel error -y -i out/test_0000-0698.mp4 -map 0:v -map 0:a -c:v libx264 -preset slow -crf 23 \
       -tune film -pix_fmt yuv420p -c:a copy -movflags +faststart out/test_0000-0698_web.mp4
ls -la out/
