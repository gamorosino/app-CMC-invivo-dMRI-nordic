#!/bin/bash
# Local CLI launcher — writes config.json then calls ./main.
# Requires: Singularity, jq.
SCRIPT=$(realpath -s "$0"); SCRIPT_DIR=$(dirname "$SCRIPT")

usage() {
  cat >&2 <<EOF
Usage: $(basename "$0") \\
  --ap_dwi <nii.gz> --ap_bvecs <file> --ap_bvals <file> \\
  --pa_dwi <nii.gz> --pa_bvecs <file> --pa_bvals <file> \\
  --total_readout_time <sec> --lower_b <int> \\
  [--ap_phase <nii.gz>] [--pa_phase <nii.gz>] \\
  [--t1 <nii.gz>] [--mode nhp|human] [--no_gpu] [--no_tractography]
EOF
  exit 1
}

ap_dwi="" ap_bvecs="" ap_bvals="" ap_phase=""
pa_dwi="" pa_bvecs="" pa_bvals="" pa_phase=""
t1="" total_readout_time="" lower_b=""
mode="nhp" no_gpu="false" run_tractography="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ap_dwi)              ap_dwi=$(realpath "$2");             shift 2 ;;
    --ap_bvecs)            ap_bvecs=$(realpath "$2");           shift 2 ;;
    --ap_bvals)            ap_bvals=$(realpath "$2");           shift 2 ;;
    --ap_phase)            ap_phase=$(realpath "$2");           shift 2 ;;
    --pa_dwi)              pa_dwi=$(realpath "$2");             shift 2 ;;
    --pa_bvecs)            pa_bvecs=$(realpath "$2");           shift 2 ;;
    --pa_bvals)            pa_bvals=$(realpath "$2");           shift 2 ;;
    --pa_phase)            pa_phase=$(realpath "$2");           shift 2 ;;
    --t1)                  t1=$(realpath "$2");                 shift 2 ;;
    --total_readout_time)  total_readout_time="$2";             shift 2 ;;
    --lower_b)             lower_b="$2";                       shift 2 ;;
    --mode)                mode="$2";                          shift 2 ;;
    --no_gpu)              no_gpu="true";                      shift   ;;
    --no_tractography)     run_tractography="false";           shift   ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

errors=0
for flag in ap_dwi ap_bvecs ap_bvals pa_dwi pa_bvecs pa_bvals total_readout_time lower_b; do
  val="${!flag}"
  [ -z "$val" ] && { echo "Error: --${flag} is required" >&2; errors=1; }
done
for flag in ap_dwi ap_bvecs ap_bvals pa_dwi pa_bvecs pa_bvals; do
  val="${!flag}"
  [ -n "$val" ] && [ ! -f "$val" ] && { echo "Error: not found: $val" >&2; errors=1; }
done
[ $errors -ne 0 ] && exit 1

jq_null_or_str() { [ -n "$1" ] && jq -n --arg v "$1" '$v' || echo "null"; }

cat > "${SCRIPT_DIR}/config.json" <<EOF
{
  "ap_dwi":   $(jq -n --arg v "$ap_dwi"   '$v'),
  "ap_bvecs": $(jq -n --arg v "$ap_bvecs" '$v'),
  "ap_bvals": $(jq -n --arg v "$ap_bvals" '$v'),
  "ap_phase": $(jq_null_or_str "$ap_phase"),
  "pa_dwi":   $(jq -n --arg v "$pa_dwi"   '$v'),
  "pa_bvecs": $(jq -n --arg v "$pa_bvecs" '$v'),
  "pa_bvals": $(jq -n --arg v "$pa_bvals" '$v'),
  "pa_phase": $(jq_null_or_str "$pa_phase"),
  "t1":       $(jq_null_or_str "$t1"),
  "total_readout_time": $total_readout_time,
  "lower_b": $lower_b,
  "mode": $(jq -n --arg v "$mode" '$v'),
  "no_gpu": $no_gpu,
  "run_tractography": $run_tractography,
  "denoise": true,
  "run_gibbs": true,
  "run_n4": true,
  "stdreg_method": "mmorf"
}
EOF

echo "config.json written:"; cat "${SCRIPT_DIR}/config.json"; echo ""
bash "${SCRIPT_DIR}/main"
