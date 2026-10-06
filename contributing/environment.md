# (re)creating a conda environment

Beacause the recipes in this cookbook are self-contained, they will have their own conda environment. The `environment.yml` file contains the necessary dependencies to run the notebook. You can create a new conda environment with the following command:

```bash
conda env export --from-history > environment.yml
```

The `--from-history` flag will only include the packages that you explicitly installed in the environment without any extra tag associated to your specific operating system. This will make it easier for others to recreate the environment in their own machine.

It is possible to "test" the `environment.yml` in different operative systems with:

```bash
CONDA_SUBDIR=win-64 conda env create -f environment.yml -n test --dry-run
CONDA_SUBDIR=osx-arm64 conda env create -f environment.yml -n test --dry-run
CONDA_SUBDIR=osx-64 conda env create -f environment.yml -n test --dry-run
CONDA_SUBDIR=linux-64 conda env create -f environment.yml -n test --dry-run
```

This won't install any packages but it will check if it's possible, given the operative system and all the package dependencies. 

:::{note}

Add the end, check that there is no `prefix` tag in the `environment.yml` file as this will include the absolute path to your current conda environment and that information is not useful for others. 

:::