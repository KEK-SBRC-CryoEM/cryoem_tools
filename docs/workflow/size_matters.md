# Size Matters workflow

Computes extraction, binning and mask parameters for the CS-Schemes template from a few values from your dataset.

## Overview

The workflow provides these CS-Schemes parameters:

```
SS_comm_class2d_pmd
SS_comm_optimal_pmd
SS_comm_lbin_angpix
GTF_lbin_extract_mics_box
GTF_lbin_extract_mics_0o95box
GTF_lbin_extract_parts_box
GTF_lbin_extract_parts_x_min
GTF_lbin_extract_parts_x_max
GTF_lbin_extract_parts_y_min
GTF_lbin_extract_parts_y_max
GTF_lbin_abinit3d_pmd
```

The user input are values from the dataset specified in the template [`emd_0407.yaml`](/automation/configs/user/emd_0407.yaml).
Details on the inputs are listed under [Your own dataset](#your-own-dataset).

## Run the example (lustre1)

```bash
module load cspa
CFG=/lustre1/emsystem/apps/cryoem_tools/automation/configs

tomato -c $CFG/user/emd_0407.yaml $CFG/system/cryowork.yaml $CFG/workflow/size_matters.yaml --verbose
```

- Results are at `./tomato/`. If that folder exists, a timestamp is added to the name; `-o <dir>` puts the results elsewhere.
- The CS-Schemes parameters are printed at the end of the message.
    - It is also possible to check it by running the command `cat tomato/cs_schemes/css_parameters/css_parameters.yaml`.
- The detailed output history of this workflow is at `tomato/pipeline_data.yaml`

## Run the steps individually

These five commands do the same as the example workflow run, one step at a time.

```bash
module load cspa
# 1. Mask of the reference map (DeepMASC; paths from system/cryowork.yaml)
mkdir -p mask
/lustre1/emsystem/apps/pyenv/versions/anaconda3-5.3.1/envs/deepmasc/bin/python \
    /lustre1/emsystem/apps/DeepMASC_2026/DeepMASC/contour.py \
    --input_map_path /lustre1/emsystem/apps/cryoem_tools/examples/size_matters/emd_0407.map --output_folder mask -a -p

# 2. Particle size from the mask -> output: diameter_A, diameter_px; input: pixel_size_A_per_px
cspa size_estimation --volume mask/prot_mask_final.mrc

# 3. Binning factor -> output.rank1: binning_factor, binned_pixel_size_A_per_px, target_resolution_A, compatible_boxes
cspa find_binning_factor --pixel_size 0.5585 --target_resolution 8

# 4. Box for the particle and its delocalized signal, at the binned pixel size -> output: delocalization_box_px
cspa size_matters --mode deloc --voltage 200 --cs 2.7 --defocus 1.5 \
    --pixel_size <binned_pixel_size_A_per_px> --resolution <target_resolution_A> --diameter <diameter_A>

# 5. CS-Schemes parameters
cspa-python $CSPA_ROOT/automation/css_parameters.py --workflow size_matters \
    --lbin_pixel_size <binned_pixel_size_A_per_px> --lbin_binning_factor <binning_factor> \
    --lbin_compatible_boxes <compatible_boxes, space-separated> --lbin_deloc_box <delocalization_box_px> \
    --particle_diameter <diameter_px> --particle_pixel_size <pixel_size_A_per_px from step 2> \
    --micrograph_upper_bound_x 3838 --micrograph_upper_bound_y 3710 --padding_percentage 0.2
```

Details of each step: [size_estimation](/docs/analyses/size_estimation.md), [find_binning_factor](/docs/analyses/find_binning_factor.md), [size_matters](/docs/analyses/size_matters.md).

## Your own dataset

Copy the template, edit the keys below, and run with your file:

```bash
cp $CFG/user/emd_0407.yaml my_dataset.yaml
tomato -c my_dataset.yaml $CFG/system/cryowork.yaml $CFG/workflow/size_matters.yaml --verbose
```

| Key | Unit | Value |
|---|---|---|
| `reference_map_filepath` | path | A map of the particle, used to measure its size. If the reference map is not available, use the following workflow: `size_matters_no_diameter.yaml`. |
| `defocus` | µm | The representative defocus in the dataset, positive for underfocus. |
| `target_resolution` | Å | Target resolution of the binned (lbin) stage; it sets the binning factor. |
| `micrograph_upper_bound_x`, `micrograph_upper_bound_y` | px | Micrograph width (x) and height (y). |
| `EM_kV`, `EM_mics_apix`, `EM_Cs` (under `em_settings`) | kV, Å/px, mm | Acceleration voltage, micrograph pixel size, spherical aberration. |
