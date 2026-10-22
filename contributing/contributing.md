---
downloads: []
---

# Contributing to the Weather Change Cookbook

For now, there is only one type of recipe in the cookbook you can contribute. A recipe will be a polished and well-documented workflow that showcase a specific data analysis technique or method. A recipe should be a self-contained example that can be run by others, and should include all necessary code, data, and documentation. In terms of data, the recipe will use a small sample dataset that can be downloaded from a public sources.

To contribute a new recipe, please follow the tutorial and open [an issue on the repository](https://github.com/21centuryweather/Weather-Change-Cookbook/issues) to discuss your idea. 

## Recipe components

And average recipe will have the following components:

```bash
cold-fronts/
├── cold-fronts-analysis.ipynb
├── download_cold-fronts.py
├── environment.yml
└── README.md
```

The `cold-fronts-analysis.ipynb` is the main notebook that contains the analysis and visualisation of the data. The `download_cold-fronts.py` script is used to download the data from a public source, for example Zenodo. The data will be downloaded on a subfolder `data` and the notebook will read it from there. The `environment.yml` file contains the necessary Python dependencies to run the notebook. The `README.md` file contains the instructions to run the notebook and download the data.

Your recipe may also need other components. For example, it may use Python scripts for functions or pre-processing the data. That's perfectly fine, the only strict rule is that you should always use **relative paths** to read, reference or import functions. The main goal is to create a self-contained example that can be reproduced without having to edit anything. 

In the following sections you will find a template notebook you can download and use to create your own recipe. The template notebook contains the necessary structure and documentation to create a new recipe. You can also find a template `README.md` file that you can use to document your recipe.