#!/bin/bash
# Mix: original voice (priority) + ducked music + SFX, then 2-pass loudness normalisation (-14 LUFS, -1.5 dBTP)
set -e
FC="[0:a]highpass=f=75,acompressor=threshold=0.12:ratio=2.5:attack=8:release=180:makeup=1.4,asplit=2[v][key];\
[1:a]volume=-2dB[mus];[mus][key]sidechaincompress=threshold=0.02:ratio=4:attack=25:release=450:knee=4[duck];\
[2:a]volume=-3dB[fx];[v][duck][fx]amix=inputs=3:normalize=0:duration=first"
ffmpeg -v error -y -i build/voice.wav -i build/music.wav -i build/sfx.wav -filter_complex "$FC[m]" -map "[m]" -ar 48000 build/premix.wav
J=$(ffmpeg -hide_banner -i build/premix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -i build/premix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -c:a pcm_s16le build/mix.wav
ffmpeg -hide_banner -i build/mix.wav -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak:"
