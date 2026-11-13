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

## Instructions to use this recipe on mybinder

To run this notebook on mybinder, click the binder badge. This will open a new browser window with a Jupyter notebook interface where you can run the code without installing the environment locally. 

Then, on the terminal inside the binder interface, run the following command to download the data:

```
python download_swt.py
```

This will create a `data/` folder with the necessary data to run the notebook.