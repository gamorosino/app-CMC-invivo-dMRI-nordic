#!/usr/bin/env python3
# brainlife.io adapter for SPMIC-UoN/CMC_invivo_dMRI_pipeline with Python NORDIC denoising.
#
# Runs Python NORDIC on each staged magnitude+phase DWI pair before handing
# data to cmc_invivo_pipeline (which then skips its own denoising step).
# Falls back to MRtrix3 MPPCA when no phase inputs are provided.
import glob
import json
import os
import shutil
import subprocess
import sys

import yaml

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = "out_dir"
WORK_DIR = os.path.abspath("work")
INPUT_ROOT = os.path.join(WORK_DIR, "input_root")
DMRI_ROOT = os.path.join(WORK_DIR, "proc")
NORDIC_SCRIPT = os.path.join(APP_DIR, "nordic", "run_nordic.py")
MPPCA_DENOISE_SH = os.path.join(APP_DIR, "denoise_mppca.sh")


def load_config():
    with open("config.json") as f:
        return json.load(f)


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def link_run(src_nii, src_bvec, src_bval, dest_dir, tag, idx):
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy2(src_nii, os.path.join(dest_dir, f"{tag}_{idx}.nii.gz"))
    shutil.copy2(src_bvec, os.path.join(dest_dir, f"{tag}_{idx}.bvec"))
    shutil.copy2(src_bval, os.path.join(dest_dir, f"{tag}_{idx}.bval"))


def build_input_root(config, tag_pos, tag_neg):
    ap_dwi, ap_bvecs, ap_bvals = (as_list(config.get(k)) for k in ("ap_dwi", "ap_bvecs", "ap_bvals"))
    pa_dwi, pa_bvecs, pa_bvals = (as_list(config.get(k)) for k in ("pa_dwi", "pa_bvecs", "pa_bvals"))

    if not (len(ap_dwi) == len(ap_bvecs) == len(ap_bvals)):
        sys.exit(f"ap_dwi/ap_bvecs/ap_bvals count mismatch: {len(ap_dwi)}/{len(ap_bvecs)}/{len(ap_bvals)}")
    if not (len(pa_dwi) == len(pa_bvecs) == len(pa_bvals)):
        sys.exit(f"pa_dwi/pa_bvecs/pa_bvals count mismatch: {len(pa_dwi)}/{len(pa_bvecs)}/{len(pa_bvals)}")
    if not ap_dwi or not pa_dwi:
        sys.exit("Both ap_dwi and pa_dwi need at least one run.")

    pos_dir = os.path.join(INPUT_ROOT, tag_pos)
    neg_dir = os.path.join(INPUT_ROOT, tag_neg)
    for i, (nii, bvec, bval) in enumerate(zip(ap_dwi, ap_bvecs, ap_bvals), start=1):
        link_run(nii, bvec, bval, pos_dir, tag_pos, i)
    for i, (nii, bvec, bval) in enumerate(zip(pa_dwi, pa_bvecs, pa_bvals), start=1):
        link_run(nii, bvec, bval, neg_dir, tag_neg, i)

    return len(ap_dwi), len(pa_dwi)


def _nordic_denoise_file(magn_path, phase_src, stem):
    """Run NORDIC on one staged magnitude file; replaces it with the denoised result."""
    tmp_dir = magn_path.replace(".nii.gz", "_nordic_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    cmd = [
        sys.executable, NORDIC_SCRIPT,
        "--mag", magn_path,
        "--phase", phase_src,
        "--out", tmp_dir,
        "--temporal_phase", "1",
        "--phase_filter_width", "10",
    ]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

    denoised = os.path.join(tmp_dir, "bold.nii.gz")
    if not os.path.isfile(denoised):
        sys.exit(f"NORDIC produced no output at {denoised}")
    shutil.move(denoised, magn_path)
    shutil.rmtree(tmp_dir)
    print(f"[nordic] denoised {stem} → {magn_path}", flush=True)


def run_nordic_if_applicable(config, ap_count, pa_count, tag_pos, tag_neg):
    """
    NORDIC-denoise staged magnitude files in-place when phase inputs are present.
    Returns True when NORDIC ran (pipeline should then skip its own denoise step).
    Requires phase to be provided for both AP and PA, or neither.
    """
    ap_phases = as_list(config.get("ap_phase"))
    pa_phases = as_list(config.get("pa_phase"))

    if not ap_phases and not pa_phases:
        return False

    if bool(ap_phases) != bool(pa_phases):
        sys.exit(
            "Phase must be provided for both AP and PA, or neither. "
            f"Got: ap_phase={'yes' if ap_phases else 'no'}, pa_phase={'yes' if pa_phases else 'no'}."
        )
    if len(ap_phases) != ap_count:
        sys.exit(f"ap_phase count ({len(ap_phases)}) != ap_dwi count ({ap_count}).")
    if len(pa_phases) != pa_count:
        sys.exit(f"pa_phase count ({len(pa_phases)}) != pa_dwi count ({pa_count}).")

    pos_dir = os.path.join(INPUT_ROOT, tag_pos)
    neg_dir = os.path.join(INPUT_ROOT, tag_neg)

    for i, phase_src in enumerate(ap_phases, start=1):
        magn = os.path.join(pos_dir, f"{tag_pos}_{i}.nii.gz")
        _nordic_denoise_file(magn, phase_src, f"{tag_pos}_{i}")

    for i, phase_src in enumerate(pa_phases, start=1):
        magn = os.path.join(neg_dir, f"{tag_neg}_{i}.nii.gz")
        _nordic_denoise_file(magn, phase_src, f"{tag_neg}_{i}")

    return True


def resolve_denoise_sh(config):
    if not config.get("denoise", True):
        return None
    custom = config.get("custom_denoise_sh")
    if custom:
        if os.path.isdir(custom):
            candidates = sorted(glob.glob(os.path.join(custom, "*.sh")))
            if not candidates:
                sys.exit(f"custom_denoise_sh ({custom}) is a directory with no .sh script.")
            return os.path.abspath(candidates[0])
        return os.path.abspath(custom)
    return MPPCA_DENOISE_SH


def write_pipeline_config(config, denoise_sh, nordic_denoised):
    # When NORDIC already ran, force denoise: false so the pipeline skips its own pass.
    run_denoise = (not nordic_denoised) and bool(config.get("denoise", True))
    cfg = {
        "dmri_root": DMRI_ROOT,
        "input_root": INPUT_ROOT,
        "mode": config.get("mode", "nhp"),
        "total_readout_time": float(config["total_readout_time"]),
        "lower_b": int(config["lower_b"]),
        "b0range": float(config.get("b0range", 60)),
        "combine_matched_flag": 1 if config.get("combine_only_matched_pairs", False) else 0,
        "ptx_steplength": float(config.get("ptx_steplength", 0.15)),
        "no_gpu": bool(config.get("no_gpu", False)),
        "denoise": run_denoise,
        "run_gibbs": bool(config.get("run_gibbs", True)),
        "run_n4": bool(config.get("run_n4", True)),
        "use_docker": False,
        "stdreg_method": config.get("stdreg_method", "mmorf"),
    }
    if run_denoise and denoise_sh:
        cfg["denoise_sh"] = denoise_sh
    if config.get("t1"):
        cfg["t1"] = config["t1"]
    if config.get("eddy_extra_args"):
        cfg["eddy_extra_args"] = config["eddy_extra_args"]

    os.makedirs(WORK_DIR, exist_ok=True)
    yaml_path = os.path.join(WORK_DIR, "invivo_dmri_config.yaml")
    with open(yaml_path, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    print(f"[main] pipeline config: {yaml_path}\n{yaml.safe_dump(cfg, sort_keys=False)}")
    return yaml_path


def run_pipeline(yaml_path, run_tractography):
    cmd = ["cmc_invivo_pipeline", yaml_path, "-v", "--preproc"]
    if run_tractography:
        cmd.append("--tractography")
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def collect_outputs(run_tractography):
    def outdir(name):
        d = os.path.join(OUT_DIR, name)
        os.makedirs(d, exist_ok=True)
        return d

    dtifit_dir = os.path.join(DMRI_ROOT, "dtifit")
    data_dir = os.path.join(DMRI_ROOT, "data")
    qa_dir = os.path.join(DMRI_ROOT, "QA")
    stdreg_dir = os.path.join(DMRI_ROOT, "stdreg")
    topup_dir = os.path.join(DMRI_ROOT, "topup")
    eddy_dir = os.path.join(DMRI_ROOT, "eddy")
    xtract_dir = os.path.join(DMRI_ROOT, "xtract")

    tdir = outdir("tensor")
    shutil.copy2(os.path.join(dtifit_dir, "dti_FA.nii.gz"), os.path.join(tdir, "fa.nii.gz"))
    shutil.copy2(os.path.join(dtifit_dir, "dti_MD.nii.gz"), os.path.join(tdir, "md.nii.gz"))
    shutil.copy2(os.path.join(dtifit_dir, "dti_L1.nii.gz"), os.path.join(tdir, "ad.nii.gz"))
    subprocess.run([
        "fslmaths", os.path.join(dtifit_dir, "dti_L2.nii.gz"),
        "-add", os.path.join(dtifit_dir, "dti_L3.nii.gz"),
        "-div", "2", os.path.join(tdir, "rd.nii.gz"),
    ], check=True)

    mdir = outdir("brain_mask")
    shutil.copy2(os.path.join(data_dir, "nodif_brain_mask.nii.gz"), os.path.join(mdir, "mask.nii.gz"))

    qdir = outdir("qa_report")
    qa_pdf = os.path.join(qa_dir, "QA_report.pdf")
    if os.path.isfile(qa_pdf):
        shutil.copy2(qa_pdf, os.path.join(qdir, "report.pdf"))
    else:
        print(f"WARNING: QA report not found at {qa_pdf}", file=sys.stderr)

    pdir = outdir("preproc_bundle")
    for name, src in (
        ("topup", topup_dir),
        ("eddy_qc", os.path.join(eddy_dir, "eddy.qc")),
        ("data", data_dir),
        ("stdreg", stdreg_dir),
        ("dtifit", dtifit_dir),
    ):
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(pdir, name), dirs_exist_ok=True)

    xdir = outdir("tractography_bundle")
    if run_tractography and os.path.isdir(xtract_dir):
        shutil.copytree(xtract_dir, os.path.join(xdir, "xtract"), dirs_exist_ok=True)


def main():
    config = load_config()
    scheme = config.get("phase_encoding_scheme", "AP_PA")
    tag_pos, tag_neg = ("AP", "PA") if scheme == "AP_PA" else ("LR", "RL")

    ap_count, pa_count = build_input_root(config, tag_pos, tag_neg)
    nordic_denoised = run_nordic_if_applicable(config, ap_count, pa_count, tag_pos, tag_neg)

    denoise_sh = None if nordic_denoised else resolve_denoise_sh(config)
    yaml_path = write_pipeline_config(config, denoise_sh, nordic_denoised)
    run_tractography = bool(config.get("run_tractography", True))
    run_pipeline(yaml_path, run_tractography)
    collect_outputs(run_tractography)


if __name__ == "__main__":
    main()
