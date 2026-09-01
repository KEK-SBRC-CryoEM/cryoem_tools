# CryoEM Tools
Python utilities for Cryogenic Electron Microscopy Single Particle Analysis.

# Installation

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

# License
- [This](https://github.com/KEK-SBRC-CryoEM/cryoem_tools) repository is under [GLP-3.0](LICENSE).

# Usage guide
- [**Find Binning Factor**](/docs/analyses/find_binning_factor.md): Find candidate binning factors with good FFT-box compatibility and with the least number of decimal places in the associated binned pixel size.
