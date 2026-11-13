# Detecting cold fronts using day-to-day difference in maximum temperature

**Pao Corrales**

## Instructions to use this recipe locally

Before running the notebook locally you will need to install the necessary dependencies and download the data. 

* Python dependencies:

```bash
conda env create -f environment.yml
conda activate cold-fronts
```
* Data:

```
python download_cold-fronts.py
```

This will create a `data/` folder with the necessary data to run the notebook.

## Instructions to use this recipe on mybinder

To run this notebook on mybinder, click the binder badge. This will open a new browser window with a Jupyter notebook interface where you can run the code without installing the environment locally. 

Then, on the terminal inside the binder interface, run the following command to download the data:

```
python download_cold-fronts.py
```

This will create a `data/` folder with the necessary data to run the notebook.
