# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: BSD-3-Clause

import os
import pytest
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import jupyter_client

NOTEBOOKS_DIR = "cpu/notebooks"

def list_notebooks(directory):
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".ipynb")
    ]

list_nb = list_notebooks(NOTEBOOKS_DIR)
list_nb = ["cpu/CPU_demos.ipynb", 
           "cpu/notebooks/steady-state_design.ipynb", 
           "cpu/notebooks/transient_simulation.ipynb", 
           "cpu/notebooks/generate_nominal_operation_data.ipynb", 
           "cpu/notebooks/generate_dysfunctional_operation_data.ipynb",
           "cpu/notebooks/same_operating_conditions_simulation.ipynb",
           "cpu/notebooks/ai_dataset_for_event_detection.ipynb",
           "cpu/notebooks/ai_training_for_event_detection.ipynb",
           "cpu/notebooks/spot_event_using_ai.ipynb",
           "cpu/notebooks/calibration_transient_basics.ipynb",
           "cpu/notebooks/calibration_broken_wo_event.ipynb",
           "cpu/notebooks/calibration_broken_with_event.ipynb",
           "cpu/notebooks/doe.ipynb",
           "cpu/notebooks/montecarlo.ipynb",
           "cpu/notebooks/solver_debugging.ipynb",
]

@pytest.fixture(scope="session")
def execute_preprocessor():
    return ExecutePreprocessor(timeout=600)

@pytest.mark.parametrize("notebook_path", list_nb)
def test_notebook_execution(execute_preprocessor, notebook_path):
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    try:
        execute_preprocessor.preprocess(
            notebook,
            {"metadata": {"path": os.path.dirname(notebook_path)}}
        )
    except Exception as e:
        pytest.fail(f"Notebook execution failed for {notebook_path}: {e}")