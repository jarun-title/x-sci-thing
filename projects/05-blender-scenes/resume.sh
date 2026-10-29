#!/usr/bin/env bash
# Render the missing frames of a shot in 20-frame chunks, so a restart loses at most one chunk.
# usage: resume.sh <shot> <total_frames>
set -u
shot=$1; total=$2; dir=/home/claude/blender-water/frames/$shot
cd /home/claude/blender-water
mkdir -p "$dir"
f=1
while [ $f -le $total ]; do
  if [ -s "$dir/f_$(printf %04d $f).png" ]; then f=$((f+1)); continue; fi
  end=$((f+19)); [ $end -gt $total ] && end=$total
  # stop the chunk early at the next frame that already exists
  g=$f; while [ $g -le $end ] && [ ! -s "$dir/f_$(printf %04d $g).png" ]; do g=$((g+1)); done; end=$((g-1))
  echo "$(date +%H:%M:%S) rendering $shot $f-$end"
  /home/claude/blender-env/bin/python scene.py "$shot" "$dir" 67 32 $f $end > "render_${shot}_$f.log" 2>&1 || { echo "render failed at $f"; exit 1; }
  f=$((end+1))
done
echo "$(date +%H:%M:%S) done: $(ls "$dir" | wc -l) frames"
