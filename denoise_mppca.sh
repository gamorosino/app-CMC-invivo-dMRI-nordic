#!/usr/bin/env bash
# MPPCA fallback denoise_sh for runs without phase data.
# Accepts the same CLI contract as SPMIC-UoN/EDDEN's 02_run_denoise.sh
# but always denoises with MRtrix3's dwidenoise (already in the container).
set -euo pipefail

usage() {
  echo "Usage: $0 -meth METH -domain DOMAIN -magn MAGN -phase PHASE -name NAME [-oPath OPATH] [-aux AUX]" >&2
  exit 2
}

magn="" ; name="" ; oPath=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -meth)   shift 2 ;;
    -domain) shift 2 ;;
    -phase)  shift 2 ;;
    -aux)    shift 2 ;;
    -magn)   magn="$2"; shift 2 ;;
    -name)   name="$2"; shift 2 ;;
    -oPath)  oPath="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[ -z "$magn" ] && { echo "ERROR: -magn is mandatory" >&2; usage; }
[ -z "$name" ] && { echo "ERROR: -name is mandatory" >&2; usage; }
[ -z "$oPath" ] && oPath="$(dirname "$magn")"
mkdir -p "$oPath"

out="${oPath}/${name}.nii.gz"
noisemap="${oPath}/${name}_noisemap.nii.gz"

echo "[denoise_mppca] dwidenoise ${magn} -> ${out}"
dwidenoise "${magn}" "${out}" -noise "${noisemap}" -force
echo "Denoising finished: ${out}"
