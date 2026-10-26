# README.md

Recipe title: Australian Synoptic Weather Types

Authors: Michael Barnes

## Instructions to use this recipe locally

Before running the notebook locally you will need to install the necessary dependencies and download the data (50 MB).

* Python dependencies:

```bash
conda env create -f environment.yml
conda activate swt
```
* Data:

```
python download_swt.py
```

This will create a `data/` folder with the necessary data to run the notebook.

* Run the recipe:

Now you have all the components of the recipe (the code and data). When running the recipe, make sure that the `synoptic-weather-types/` folder is the working directory, by opening that folder in your preferred Python GUI.


## Instructions to use this recipe on mybinder

To run this notebook on mybinder, click the binder badge. This will open a new browser window with a Jupyter notebook interface where you can run the code without installing the environment locally. 

Then, on the terminal inside the binder interface, run the following command to download the data:

```
python download_swt.py
```

This will create a `data/` folder with the necessary data to run the notebook.