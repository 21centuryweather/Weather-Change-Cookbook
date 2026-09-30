---
downloads:
  - file: ./README.md
    title: Download template
---
# README.md

Include the title of the recipe and the author(s). Following there is a very simple example of instructions. Your recipe may need extra things, add here everything you think it may be useful for someone trying to run the code in the notebook. 

## Instructions to use this recipe

Before running the notebook locally you will need to install the necessary dependencies and download the data. 

* Python dependencies:

```bash
conda env create -f environment.yml
conda activate <name of your recipe>
```
* Data:

```
python download_<name of your recipe>.py
```

This will create a `data/` folder with the necessary data to run the notebook.