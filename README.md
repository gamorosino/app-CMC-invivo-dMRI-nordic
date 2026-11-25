<h1 align="center">CMC invivo dMRI (NORDIC)</h1>

<p align="center">
  Preprocesses in-vivo diffusion MRI (macaque 10.5T by default, or human) with the CMC pipeline: NORDIC or MPPCA denoising, Gibbs and N4 correction, TOPUP/EDDY, DTI fitting, standard-space registration and optional BedpostX + XTRACT tractography, with a QA report.
</p>

<p align="center">
  <a href="https://github.com/brainlife/abcd-spec"><img src="https://img.shields.io/badge/ABCD_Spec-v1.1-green.svg" alt="ABCD Spec v1.1"></a>
  <a href="https://doi.org/10.25663/brainlife.app.993"><img src="https://img.shields.io/badge/Brainlife-brainlife.app.993-blue.svg" alt="Run on brainlife.io"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-see_LICENSE-lightgrey.svg" alt="License"></a>
</p>

## At a glance

<!-- brainlife-app:begin (generated from the App manifest; edit the manifest, not this block) -->

> **Preprocesses in-vivo diffusion MRI (macaque 10.5T by default, or human) with the CMC pipeline: NORDIC or MPPCA denoising, Gibbs and N4 correction, TOPUP/EDDY, DTI fitting, standard-space registration and optional BedpostX + XTRACT tractography, with a QA report.**

Wraps the SPMIC-UoN CMC_invivo_dMRI_pipeline (Warrington et al.) with a Python NORDIC implementation. AP and PA runs (one or more each) are denoised with NORDIC when matching phase images are given, otherwise with MRtrix3 dwidenoise (MPPCA), then corrected with TOPUP/EDDY (GPU by default), fitted with DTI on the lower shell, registered to standard space (MMORF or FNIRT; NMT template in nhp mode) and optionally run through BedpostX and XTRACT. Requires both phase-encoding directions and the total readout time; expect long run times.

| | |
|---|---|
| **Inputs** | `neuro/dwi` ×2 · `neuro/dwi` (optional) ×2 · `neuro/anat/t1w` (optional) |
| **Outputs** | `neuro/tensor` · `neuro/mask` · `report/pdf` · `raw` ×2 |
| **Container** | `gamorosino/app-cmc-invivo-nordic:v1.0` |
| **Resources** | 32 GB memory · 24 h walltime |
| **Run it** | [doi.org/10.25663/brainlife.app.993](https://doi.org/10.25663/brainlife.app.993) |

#### Inputs

| Input | Datatype | Required | Description |
|---|---|---|---|
| `ap_dwi` | `neuro/dwi` | yes | AP (or LR) phase-encoding direction diffusion MRI. |
| `pa_dwi` | `neuro/dwi` | yes | PA (or RL) phase-encoding direction diffusion MRI. |
| `ap_phase` | `neuro/dwi` (phase) | no | AP phase images for NORDIC denoising. Must match ap_dwi count. Requires pa_phase. |
| `pa_phase` | `neuro/dwi` (phase) | no | PA phase images for NORDIC denoising. Must match pa_dwi count. Requires ap_phase. |
| `t1` | `neuro/anat/t1w` | no | T1w structural image for standard-space registration (optional). |

#### Outputs

| Output | Datatype | Description |
|---|---|---|
| `tensor` | `neuro/tensor` | DTI tensor-derived scalar maps (FA, MD, AD, RD) from the lower-shell tensor fit. |
| `brain_mask` | `neuro/mask` | Final post-EDDY brain mask. |
| `qa_report` | `report/pdf` | Multi-page QA report (EDDY QC, masks, tensor maps, registration, XTRACT summary). |
| `preproc_bundle` | `raw` | Full preprocessing bundle: TOPUP/EDDY outputs, final 4D data, standard-space warps. |
| `tractography_bundle` | `raw` | BedpostX + XTRACT outputs. Empty if run_tractography was disabled. |

<details>
<summary><b>Parameters</b> (14)</summary>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `total_readout_time` | number | `0.05` | Total EPI readout time in seconds (FSL convention). |
| `lower_b` | integer | `1000` | b-value threshold separating the lower shell used for tensor fitting. |
| `mode` | string | `nhp` | Pipeline mode: 'nhp' for non-human primate, 'human' for human. |
| `b0range` | number | `60` | b-value ceiling for volumes treated as b0. |
| `phase_encoding_scheme` | string | `AP_PA` | Phase-encoding axis pair: 'AP_PA' or 'LR_RL'. |
| `combine_only_matched_pairs` | boolean | `false` | Combine only AP/PA runs that are matched pairs. |
| `ptx_steplength` | number | `0.15` | Probabilistic tractography step length (mm). |
| `no_gpu` | boolean | `false` | Disable GPU acceleration (e.g. for EDDY). |
| `denoise` | boolean | `true` | Enable denoising. NORDIC runs automatically when phase inputs are provided; MPPCA is used otherwise. Set false to skip denoising entirely. |
| `run_gibbs` | boolean | `true` | Apply Gibbs ringing correction after denoising. |
| `run_n4` | boolean | `true` | Apply N4 bias field correction. |
| `run_tractography` | boolean | `true` | Run BedpostX + XTRACT tractography after preprocessing. |
| `stdreg_method` | string | `mmorf` | Standard-space registration method: 'mmorf' or 'fnirt'. |
| `eddy_extra_args` | string |  | Extra arguments passed verbatim to EDDY (optional). |

</details>

<!-- brainlife-app:end -->

## Running the App

### On brainlife.io

Open the App at [doi.org/10.25663/brainlife.app.993](https://doi.org/10.25663/brainlife.app.993), choose `neuro/dwi`, `neuro/dwi`, `neuro/dwi`, `neuro/dwi`, `neuro/anat/t1w` from your project, set the parameters and press **Execute**. The results are saved to your project as `neuro/tensor`, `neuro/mask`, `report/pdf`, `raw`, `raw`.

### Locally

You need [Singularity/Apptainer](https://apptainer.org/) (the App runs in `gamorosino/app-cmc-invivo-nordic:v1.0`), [`jq`](https://jqlang.github.io/jq/).

1. Clone this repository.
2. Create `config.json` with the paths to your inputs and the parameters:

   ```json
   {
       "ap_dwi": "/path/to/ap_dwi/ap_dwi",
       "ap_bvecs": "/path/to/ap_dwi/ap_bvecs",
       "ap_bvals": "/path/to/ap_dwi/ap_bvals",
       "pa_dwi": "/path/to/pa_dwi/pa_dwi",
       "pa_bvecs": "/path/to/pa_dwi/pa_bvecs",
       "pa_bvals": "/path/to/pa_dwi/pa_bvals",
       "ap_phase": "/path/to/ap_phase/ap_phase",
       "pa_phase": "/path/to/pa_phase/pa_phase",
       "t1": "/path/to/t1/t1",
       "total_readout_time": 0.05,
       "lower_b": 1000,
       "mode": "nhp",
       "b0range": 60,
       "phase_encoding_scheme": "AP_PA",
       "combine_only_matched_pairs": false,
       "ptx_steplength": 0.15,
       "no_gpu": false,
       "denoise": true,
       "run_gibbs": true,
       "run_n4": true,
       "run_tractography": true,
       "stdreg_method": "mmorf",
       "eddy_extra_args": ""
   }
   ```

3. Run `./main`.

## Troubleshooting

- **Both ap_dwi and pa_dwi need at least one run.**: Provide at least one AP and one PA DWI run.
- **ap_dwi/ap_bvecs/ap_bvals count mismatch**: Provide matching numbers of images, bvecs and bvals for each direction.

## Denoising

| Phase inputs provided | Method |
|---|---|
| Both `ap_phase` and `pa_phase` | **NORDIC** (magnitude + complex-domain) |
| Neither | **MPPCA** via MRtrix3 `dwidenoise` |

NORDIC runs per magnitude+phase pair before the CMC pipeline, replacing the staged
magnitude files with denoised versions. The pipeline's own denoise step is then
skipped automatically.

## `main_cli.sh` (optional convenience wrapper)

```bash
./main_cli.sh \
  --ap_dwi path/to/ap.nii.gz --ap_bvecs path/to/ap.bvecs --ap_bvals path/to/ap.bvals \
  --pa_dwi path/to/pa.nii.gz --pa_bvecs path/to/pa.bvecs --pa_bvals path/to/pa.bvals \
  [--ap_phase path/to/ap_phase.nii.gz] \
  [--pa_phase path/to/pa_phase.nii.gz] \
  --total_readout_time 0.05 --lower_b 1000
```

## Known limitations

- **Phase images**: NORDIC requires both AP and PA phase DWIs. If only one direction
  is available, the app falls back to MPPCA for all runs.
- **Not yet run end-to-end** against real macaque AP/PA acquisition data with phase.
  Treat the first real submission as the actual test.
- **GPU**: `no_gpu: false` requires a GPU-enabled resource. The `--nv` Singularity flag
  is set in `main` for GPU pass-through.
- **NORDIC license**: NORDIC is copyrighted by Regents of the University of Minnesota
  (US 10,768,260), licensed for educational/research use by non-profit institutions
  and US government agencies only. See `copyright.txt`.

## Container

The image `gamorosino/app-cmc-invivo-nordic:v1.0` is built from the `Dockerfile`
in this repo:
```
FROM swarrington1/cmc-invivo:v0.1.0
+ JAX, nibabel, scipy, numpy, matplotlib
+ NORDIC Python source (nordic/)
```

Build and push:
```bash
docker build -t gamorosino/app-cmc-invivo-nordic:v1.0 .
docker push gamorosino/app-cmc-invivo-nordic:v1.0
```

## Citing

If you use this App, please cite it, the software it builds on and brainlife.io:

- CMC invivo dMRI (NORDIC). brainlife.io App. [doi:10.25663/brainlife.app.993](https://doi.org/10.25663/brainlife.app.993)
- Jenkinson et al. FSL. *NeuroImage* 62:782-790 (2012). [doi:10.1016/j.neuroimage.2011.09.015](https://doi.org/10.1016/j.neuroimage.2011.09.015)
- Tournier et al. MRtrix3: A fast, flexible and open software framework for medical image processing and visualisation. *NeuroImage* 202:116137 (2019). [doi:10.1016/j.neuroimage.2019.116137](https://doi.org/10.1016/j.neuroimage.2019.116137)
- Hayashi S, Caron BA, Heinsfeld AS, et al. brainlife.io: a decentralized and open-source cloud platform to support neuroscience research. *Nature Methods* 21:809–813 (2024). [doi:10.1038/s41592-024-02237-2](https://doi.org/10.1038/s41592-024-02237-2)
- Avesani P, McPherson B, Hayashi S, et al. The open diffusion data derivatives, brain data upcycling via integrated publishing of derivatives and reproducible open cloud services. *Scientific Data* 6:69 (2019). [doi:10.1038/s41597-019-0073-y](https://doi.org/10.1038/s41597-019-0073-y)

## Authors

- Gabriele Amorosino

## License

See [LICENSE](LICENSE).
