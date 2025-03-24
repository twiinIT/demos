# twiinIT CPU demos

This is a repository for twiinIT's CPU demo.


## Create project environment

It is necessary to create a software environment containing the required dependencies to operate the project. \
Please ensure that you have already [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html) installed prior to do this step.

The environment is created by running at the project root:

```
micromamba create -f environment.yml
micromamba activate cpu-demos
pip install .
```

To use the project for development, install the project in the editable mode:
```
pip install -e .
```

## How to use it 

All CPU demos are presented in [notebooks](./cpu/notebooks/) and can be sequentially runned from the [descriptive notebook](./cpu/CPU_demos.ipynb).
