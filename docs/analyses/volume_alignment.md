# Volume Alignment

Align a cryo-EM volume (`.mrc`) to the box orthogonal axes based on its shape: the longest dimension of the particle along X, the middle one along Y, and the shortest along Z. Looking down Z, which is the default view in ChimeraX, shows the particle's largest view.

## Overview

The user provides either:

- a volume and a segmentation threshold; or
- a volume and a binary mask (hard mask: 1 inside, 0 outside, no soft edge).

The segmentation, from the threshold or the mask, defines the particle's shape. The script outputs the rotated and centered volume so that:

- **X** is the longest axis of the particle,
- **Y** is the middle axis,
- **Z** is the shortest axis, so the XY plane shows the largest view,
- the particle is centered in the box.

The alignment is a proper rotation, so the hand of the map is never inverted.

## Usage

```bash
python volume_alignment.py --volume <path/to/volume.mrc> --mask <path/to/mask.mrc>
python volume_alignment.py --volume <path/to/volume.mrc> --threshold <threshold>
```

For example:

```bash
# Align using a mask
python volume_alignment.py --volume map.mrc --mask mask.mrc  --output-dir results

# Align using a segmentation threshold
python volume_alignment.py --volume map.mrc --threshold 0.02 --output-dir results
```

### Required Arguments

| Argument | Description |
| --- | --- |
| `-v`, `--volume` | Volume filepath (`.mrc`) |

And one of:

| Argument | Description |
| --- | --- |
| `-m`, `--mask` | Binary mask filepath (`.mrc`) |
| `-t`, `--threshold` | Density threshold for segmenting the volume (default: `0`) |

### Optinal Argument
| Argument | Description |
| --- | --- |
| `-s`, `--save` | Save orthogonal slices (XY, XZ, YZ) of the aligned volume (`.png`) |

### Additional arguments

| Argument       | Description                   |
| -------------- | ----------------------------- |
| `--verbose`    | Enable verbose logging.       |
| `--output-dir` | Specify a directory to enable saving the output. If not provided, results print to stdout and logs to stderr only. If provided, a subdirectory named `volume_alignment` will be created under this specified directory. If it already exists, a unique suffix is appended. | 

## Outputs

Written to `<output-dir>/volume_alignment/`:

| File | Description |
| --- | --- |
| `aligned_<volume>.mrc` | The aligned volume. |
| `aligned_<mask>.mrc`   | The segmentation, aligned with the same transform. |
| `orthogonal_view.png`  | Orthogonal slices of the aligned volume (with `--save`). |

If the segmentation is empty (no voxels above the threshold), the script raises an error. Please check if the input threshold value.

## Technical overview

The volume alignment follows 5 steps:

1. **Segmentation.** PCA is applied to the coordinates of the segmented voxels, not to their density values, so the alignment depends only on the shape of the particle. With a binary mask, the mask's voxels are used directly. With a threshold, the volume is segmented first: voxels below the threshold are set to 0, and voxels at or above it to 1.

2. **Center.** The particle center is placed at the center of the box. There are two options to identify the center: (1) the mean position of the segmented voxels; or the (2) center of the sphere enclosing the voxels.

3. **Principal axes.** PCA of the voxel coordinates gives three axes (longest, intermediate and shortest views). They are placed along X, Y and Z respectively, so the XY plane, which ChimeraX shows by default, shows the largest view.

4. **Axis directions.** PCA gives each axis only as a line: it can't tell, for example, the particle's top from its bottom. To obtain the directions, the two axes with the largest skewness are pointed toward their positive skewness (the longer tail). The third axis is oriented so that the frame is right-handed (det > 0), which prevents mirroring.

5. **Alignment.** The volume is rotated and centered in a single resampling step with cubic interpolation, keeping the box size and voxel size.

This alignment method follows the PCA-based pose normalization described in:
- Vranic, D. V., Saupe, D., & Richter, J. (2001). **Tools for 3D-object retrieval: Karhunen-Loeve transform and spherical harmonics.** *In 2001 IEEE Fourth Workshop on Multimedia Signal Processing* (pp. 293-298). IEEE.
- Chaouch, M., & Verroust-Blondet, A. (2009). **Alignment of 3D models.** *Graphical Models*, 71(2), 63-76.

The core idea is the same with a few differences. These works align surface meshes and normalize their scale, whereas we use the voxels of a segmented map and keep its scale. Most importantly, the axis directions are chosen by skewness rather than by a signed second moment, and only proper rotations are used (no reflection).

## Limitations
Todo.

