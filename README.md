# app-CMC-invivo-dMRI-nordic

CMC in-vivo macaque (10.5T) diffusion MRI pipeline with native Python NORDIC denoising:
denoise (NORDIC or MPPCA), TOPUP/EDDY, DTI fitting, NMT registration, BedpostX + XTRACT
tractography, QA report.

Wraps [SPMIC-UoN/CMC_invivo_dMRI_pipeline](https://github.com/SPMIC-UoN/CMC_invivo_dMRI_pipeline)
(Warrington et al.) via `swarrington1/cmc-invivo:v0.1.0`, extended with Python
[NORDIC-python](https://github.com/JimJam07/NORDIC-python) denoising. Container:
`gamorosino/app-cmc-invivo-nordic:v1.0`.

## Denoising

| Phase inputs provided | Method |
|---|---|
| Both `ap_phase` and `pa_phase` | **NORDIC** (magnitude + complex-domain) |
| Neither | **MPPCA** via MRtrix3 `dwidenoise` |

NORDIC runs per magnitude+phase pair before the CMC pipeline, replacing the staged
magnitude files with denoised versions. The pipeline's own denoise step is then
skipped automatically.

## Inputs

- `ap_dwi` (neuro/dwi) — AP diffusion MRI (one or more runs)
- `pa_dwi` (neuro/dwi) — PA diffusion MRI (one or more runs)
- `ap_phase` (neuro/dwi, tag: phase) — AP phase images for NORDIC **[optional]**
- `pa_phase` (neuro/dwi, tag: phase) — PA phase images for NORDIC **[optional]**
- `t1` (neuro/anat/t1w) — T1w for standard-space registration **[optional]**

## Outputs

- `tensor` (neuro/tensor) — FA, MD, AD, RD maps from lower-shell DTI fit
- `brain_mask` (neuro/mask) — post-EDDY brain mask
- `qa_report` (report/pdf) — multi-page QA report
- `preproc_bundle` (raw) — TOPUP/EDDY outputs, final 4D data, standard-space warps
- `tractography_bundle` (raw) — BedpostX + XTRACT outputs (empty if `run_tractography: false`)

## Usage

**On brainlife.io:** run via `faber-app-run` or the web UI once the app is registered
and enabled on a compute resource.

**Locally:** copy `config.json.example` to `config.json`, fill in real file paths, then:

```bash
./main
```

Requires Singularity. No local Python/FSL/MRtrix3 install needed — the container
provides everything.

### `main_cli.sh` (optional convenience wrapper)

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

## Authors

- Gabriele Amorosino <gabriele.amorosino@utexas.edu>

## License

MIT, see `LICENSE`. Upstream CMC pipeline: see SPMIC-UoN/CMC_invivo_dMRI_pipeline.
NORDIC: see `copyright.txt` and the NORDIC-python repository.
