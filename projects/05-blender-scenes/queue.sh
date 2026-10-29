#!/usr/bin/env bash
# Render every remaining 3D shot in order. Each script skips frames already on disk, so this can be
# re-run after a restart or a time limit and it carries on where it stopped.
set -u
cd /home/claude/blender-water
PY=/home/claude/blender-env/bin/python
rm -f frames/*/*.tmp.png
echo "$(date +%H:%M) atom";      $PY atom_anim.py frames/atom 67 32 1 150 >> render_atom.log 2>&1 || { echo atom failed; exit 1; }
echo "$(date +%H:%M) cool";      SCENE=cool $PY scene_mol.py frames/cool 67 32 1 210 >> render_cool.log 2>&1 || { echo cool failed; exit 1; }
# heat scene, colour fix: frames 1-115 re-rendered into heat2; 116-210 are unchanged and copied over
echo "$(date +%H:%M) heat fix";  SCENE=heat $PY scene_mol.py frames/heat2 67 32 1 115 >> render_heat2.log 2>&1 || { echo heat fix failed; exit 1; }
for f in $(seq 116 210); do n=$(printf %04d $f); [ -s frames/heat2/f_$n.png ] || cp frames/heat/f_$n.png frames/heat2/f_$n.png; done
for d in atom cool heat2; do echo "$d: $(ls frames/$d | grep -v tmp | wc -l) frames"; done
echo "$(date +%H:%M) all done"
