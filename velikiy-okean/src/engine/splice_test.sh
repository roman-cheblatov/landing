#!/usr/bin/env bash
# Splice: frames 0-140 from the first test render (stream copy, cut at the IDR frame 141) + re-rendered 141-698.
set -euo pipefail
cd "$(dirname "$0")/../.."
ffmpeg -hide_banner -loglevel error -y -i work/test/test_video.mp4 -map 0:v -frames:v 141 -c copy work/test/test_seg000.mp4
printf "file 'test_seg000.mp4'\nfile 'test_seg141.mp4'\n" > work/test/concat.txt
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i work/test/concat.txt -c copy work/test/test_video_v2.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,duration -of compact work/test/test_video_v2.mp4
mv work/test/test_video.mp4 work/test/test_video_v1.mp4
mv work/test/test_video_v2.mp4 work/test/test_video.mp4
