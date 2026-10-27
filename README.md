# CryoEM Tools
Python utilities for Cryogenic Electron Microscopy Single Particle Analysis.

# Installation

**Requirements**
- [conda](https://docs.conda.io)
- git

## Python package
```bash
# Get the source code
git clone https://github.com/KEK-SBRC-CryoEM/cryoem_tools.git
cd cryoem_tools

# Create a conda environment
conda create -n cspa python=3.14
conda activate cspa

# Install the code as a package
pip install -e .
```

## *(optional)* Environment module for cluster/HPC
Expose `cspa` commands by `module load cspa`.
- Required: [Environment Modules](https://modules.readthedocs.io).

**1. Modulefile** 

Copy the template file into your `MODULEPATH` directory:
   
```bash
cp /path/to/cryoem_tools/modulefiles/cspa_template /path/to/modulefiles/cspa
```

Then edit the two paths at the top (repository and python):

```tcl
set root   /path/to/cryoem_tools
set python /path/to/envs/cspa/bin/python
```

To find the Python path, run `conda activate cspa`, then `which python`.

**2. Make the commands executable**

```bash
cd /path/to/cryoem_tools
chmod +x bin/cspa bin/cspa-python bin/cspa-viewer
```

**3. Check.**

```bash
module load cspa
cspa --help
```

This module provides three commands, with tab completion for `cspa` in bash:
- `cspa <analysis> [options]`: run an analysis (`cspa` alone lists them);
- `cspa-python`: python of the `cspa` environment; and
- `cspa-viewer <path/to/image>`: a simple image viewer for X11 forwarding (`ssh -X`).

# License
- [This](https://github.com/KEK-SBRC-CryoEM/cryoem_tools) repository is under [GPL-3.0](LICENSE).

# Usage guide
- [**Find Binning Factor**](/docs/analyses/find_binning_factor.md): Find candidate binning factors with good FFT-box compatibility and with the least number of decimal places in the associated binned pixel size.
- [**Volume Alignment**](/docs/analyses/volume_alignment.md): Standardizes the pose of a cryo-EM volume (`.mrc`) by aligning it to the orthogonal axes so the longest view is on the XY plane (view from Z) and the shortest view on YZ (view from X).