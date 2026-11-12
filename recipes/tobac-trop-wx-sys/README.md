# Using the `tobac` algorithm to identify and track tropical synoptic weather systems

**M. Reyhan Respati**

This recipe is a demonstration of the weather system detection methods employed in [Respati et al. (2026)](https://doi.org/10.5194/wcd-7-2171-2026).

## Before using this recipe

- You need to install the required `python` packages by running the following commands:

```
conda env create -f environment.yaml
conda activate tobac_training
```

- After setting up the `conda` environment, you need to download the data by running the `download_data.py` script:

```
python download_data.py
```

This script should create a `data/` directory containing 5 (five) `netcdf` (`.nc`) files.
