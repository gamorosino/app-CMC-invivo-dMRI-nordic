#!/usr/bin/env python3
"""Brainlife CLI wrapper around NORDIC-python (https://github.com/JimJam07/NORDIC-python)."""
import argparse
import os
import shutil

from nordic import Nordic

p = argparse.ArgumentParser()
p.add_argument("--mag", required=True)
p.add_argument("--phase", default="")
p.add_argument("--out", default="out")
p.add_argument("--temporal_phase", type=int, default=1)
p.add_argument("--phase_filter_width", type=int, default=10)
p.add_argument("--save_gfactor_map", type=int, default=0)
a = p.parse_args()

os.makedirs(a.out, exist_ok=True)
args = {
    "temporal_phase": a.temporal_phase,
    "phase_filter_width": a.phase_filter_width,
    "save_gfactor_map": a.save_gfactor_map,
    "write_gzipped_niftis": 1,
    "FN_OUT": "bold",
    "DIROUT": os.path.abspath(a.out) + "/",
}
if not a.phase:
    args["magnitude_only"] = 1
Nordic(a.mag, a.phase or a.mag, Args=args)
