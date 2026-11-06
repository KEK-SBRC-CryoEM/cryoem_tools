# Size Matters

Help choosing a box size for particle extraction, from the microscope settings and the pixel size.

## Overview

A box needs to:

1. **Provide enough sampling points of the CTF in Fourier space.**
2. **Include the delocalized signal in real space.** 

**(1) CTF sampling** (`--mode ctf`)

*I have a box: up to what resolution can it represent the CTF without aliasing?*

**Method:** Penczek's CTF limit (fixed version). Given the box size, it returns the highest resolution before the CTF aliases.

**(2) Delocalization** (`--mode deloc`)

*For a target resolution, what is the ideal box size?*

**Method:** derivative of the CTF phase. Given the target resolution, it returns the box size that holds the particle plus its delocalized signal. If the particle diameter is not known yet, the box covers only the delocalized signal at the center.

## Usage

```bash
python size_matters.py --mode ctf   --box_size <BOX_SIZE> --pixel_size <PIXEL_SIZE> --voltage <VOLTAGE> --defocus <DEFOCUS>
python size_matters.py --mode deloc --resolution <RESOLUTION> --pixel_size <PIXEL_SIZE> --voltage <VOLTAGE> --defocus <DEFOCUS> [--diameter <DIAMETER>]
```

Examples:

```bash
# Resolution before CTF aliasing in a 480 px box
python size_matters.py --mode ctf --voltage 200 --defocus 1.7 --cs 2.7 --pixel_size 0.5585 --box_size 480

# Box size for 2.7 Å, particle diameter not known yet
python size_matters.py --mode deloc --voltage 200 --defocus 1.7 --cs 2.7 --pixel_size 0.5585 --resolution 2.7

# Box size for 2.7 Å and a 76 Å particle
python size_matters.py --mode deloc --voltage 200 --defocus 1.7 --cs 2.7 --pixel_size 0.5585 --resolution 2.7 --diameter 80

# Both ctf and deloc methods
python size_matters.py --mode all --voltage 200 --defocus 1.7 --cs 2.7 --pixel_size 0.5585 --resolution 2.7 --diameter 80 --box_size 480
```

### Required arguments

| Argument       | Short | Description                                |
| -------------- | ----- | ------------------------------------------ |
| `--mode`       | `-m`  | `ctf`, `deloc` or `all`                    |
| `--voltage`    | `-k`  | Acceleration voltage [kV]                  |
| `--defocus`    | `-d`  | Defocus [µm], positive for underfocus      |
| `--cs`         | `-c`  | Spherical aberration [mm] (default: `2.7`) |
| `--pixel_size` | `-p`  | Pixel size [Å/px]                          |

### Arguments by mode

| Argument       | Short | Mode              | Description   |
| -------------- | ----- | ----------------- | ------------- |
| `--box_size`   | `-b`  | `ctf`             | Box size [px] |
| `--resolution` | `-r`  | `deloc`           | Target resolution [Å] |
| `--diameter`   | `-D`  | `deloc`, optional | Particle diameter [Å] (default: `0`). With `0`, the box covers only the delocalization. |

`--mode all` requires the arguments of both modes.

### Additional arguments

| Argument       | Description                   |
| -------------- | ----------------------------- |
| `--json`       | Print the results as JSON instead of YAML. Useful for the automation pipeline. |
| `--verbose`    | Enable verbose logging.       |
| `--output-dir` | Specify a directory to enable saving the output. If not provided, results print to stdout and logs to stderr only. If provided, a subdirectory named `size_matters` will be created under this specified directory. If it already exists, a unique suffix is appended. |

## Outputs

The results are printed to stdout, as YAML by default or as JSON with `--json`. With `--output-dir`, they are also written to `<output-dir>/size_matters/`:

| Variable                             | Mode    | Description |
| ------------------------------------ | ------- | --- |
| `ctf_limit_resolution_A`             | `ctf`   | Highest resolution [Å] before the CTF aliases in the box |
| `ctf_limit_frequency_per_A`          | `ctf`   | The same limit as a spatial frequency [Å⁻¹] |
| `ctf_limit_fourier_bin`              | `ctf`   | Fourier pixel index, from 0 at the center to half the box size at Nyquist |
| `delocalization_max_width_A`         | `deloc` | Largest delocalization R [Å] up to the target resolution: how far the signal shifts beyond the particle's edge |
| `delocalization_max_frequency_per_A` | `deloc` | Spatial frequency [Å⁻¹] where R occurs: the target, or lower when spherical aberration starts to cancel the defocus shift |
| `delocalization_box_px`              | `deloc` | Box size [px] that holds the particle plus its delocalized signal, rounded up to an even number |

### Example

```bash
python size_matters.py --mode all --voltage 200 --defocus 1.7 --cs 2.7 --pixel_size 0.5585 --resolution 2.7 --diameter 80 --box_size 480
```

```yaml
input:
  voltage_kV: 200.0
  lambda_A: 0.025078469648974467
  defocus_um: 1.7
  cs_mm: 2.7
  box_size_px: 480
  pixel_size_A: 0.5585
  particle_diameter_A: 80.0
  target_resolution_A: 2.7
output:
  ctf_limit_resolution_A: 2.7637113402061857
  ctf_limit_frequency_per_A: 0.3618322888689943
  ctf_limit_fourier_bin: 97
  delocalization_max_width_A: 136.26554568224165
  delocalization_max_frequency_per_A: 0.37037037037037035
  delocalization_box_px: 632
```

For a 2.7 Å target, this 480 px box satisfies neither requirement: it samples the CTF only up to 2.76 Å (1), and the delocalized signal needs 626 px (2).

## Technical Overview
todo

## References
todo