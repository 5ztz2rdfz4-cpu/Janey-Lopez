#!/bin/bash
# 2700 frames (90s @30fps) split over 4 headless Chromium workers, then concatenated
set -e
N=2700; K=4; STEP=$((N/K))
for i in $(seq 0 $((K-1))); do
  node render.js video $((i*STEP)) $(((i+1)*STEP)) build/seg/s$i.mp4 > build/seg/log$i.txt 2>&1 &
done
wait
for i in $(seq 0 $((K-1))); do echo "file 's$i.mp4'"; done > build/seg/list.txt
ffmpeg -v error -y -f concat -safe 0 -i build/seg/list.txt -c copy build/video_noaudio.mp4
echo RENDER_DONE
