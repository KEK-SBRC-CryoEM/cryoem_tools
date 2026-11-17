# Size Estimation

Estimate the particle size from a cryo-EM map or mask (`.mrc`), as the smallest sphere enclosing the density volume.

## Overview

The user provides either:

- a map and a segmentation threshold; or
- a mask of the particle.

The volume is segmented with the threshold, or the mask is used as the segmentation. Then, size is estimated as the diameter of the smallest sphere enclosing the segmented area. Before fitting the sphere, the segmentation is lightly smoothed using a guassian filter and cleaned with a binary opening and closing operations. 

- its **diameter** estimates the particle size, in pixels and in Å;
- its **center** gives the particle's position in the box.

## Usage

```bash
python size_estimation.py --volume <path/to/volume.mrc> --threshold <threshold>
python size_estimation.py --volume <path/to/mask.mrc>
```

For example:

```bash
# Size from a map, segmented at a threshold
python size_estimation.py --volume postprocess.mrc --threshold 0.0143

# Size from a mask, saving the sphere as a mask for a visual check
python size_estimation.py --volume mask.mrc --save --output-dir results
```

### Required arguments

| Argument   | Short | Description                      |
| ---------- | ----- | -------------------------------- |
| `--volume` | `-v`  | Volume or mask filepath (`.mrc`) |

### Optional arguments

| Argument      | Short | Description |
| ------------- | ----- | ----------- |
| `--threshold` | `-t`  | Density threshold for segmenting a map (default: `0`). Not needed for a mask. |
| `--save`      | `-s`  | Save the enclosing sphere as a mask (`.mrc`), for a visual check against the map |

### Additional arguments

| Argument       | Description                   |
| -------------- | ----------------------------- |
| `--json`       | Print the results as JSON instead of YAML. Useful for the automation pipeline. |
| `--verbose`    | Enable verbose logging.       |
| `--output-dir` | Specify a directory to enable saving the output. If not provided, results print to stdout and logs to stderr only. If provided, a subdirectory named `size_estimation` will be created under this specified directory. If it already exists, a unique suffix is appended. |

## Output

| Layer    | Variable              | Description |
| -------- | --------------------- | ----------- |
| `input`  | `volume_filepath`     | Volume or mask filepath (`--volume`) |
| `input`  | `threshold`           | Segmentation threshold (`--threshold`) |
| `input`  | `box_size_px`         | Box size of the input [px] |
| `input`  | `pixel_size_A_per_px` | Pixel size of the input [Å/px], from the file header |
| `output` | `center_zyx_px`       | Center of the sphere [px], as array indices in (z, y, x) order. |
| `output` | `radius_px`           | Radius of the sphere [px] |
| `output` | `diameter_px`         | Diameter of the sphere [px] |
| `output` | `radius_A`            | Radius of the sphere [Å] |
| `output` | `diameter_A`          | Diameter of the sphere [Å]: the estimated particle size |
| `output` | `mask_filepath`       | Path of the sphere mask with `--save`, otherwise `null` |

