# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: BSD-3-Clause


from pathlib import Path

import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"


list_nb = [
    "steady-state_design.ipynb",
    "transient_simulation.ipynb",
    "generate_nominal_operation_data.ipynb",
    "generate_dysfunctional_operation_data.ipynb",
    "same_operating_conditions_simulation.ipynb",
    "ai_dataset_for_event_detection.ipynb",
    "ai_training_for_event_detection.ipynb",
    "spot_event_using_ai.ipynb",
    "calibration_transient_basics.ipynb",
    "calibration_broken_wo_event.ipynb",
    "calibration_broken_with_event.ipynb",
    "doe.ipynb",
    "montecarlo.ipynb",
    "solver_debugging.ipynb",
    "Parametric_geometry.ipynb",
]


@pytest.fixture(scope="session")
def execute_preprocessor():
    """Return a preprocessor that can execute notebooks."""
    return ExecutePreprocessor(timeout=600)


@pytest.mark.notebooks
@pytest.mark.parametrize("notebook_path", list_nb)
def test_notebook_execution(execute_preprocessor, notebook_path):
    """Test that the notebook can be executed without error."""
    notebook_full_path = NOTEBOOKS_DIR / notebook_path

    # Read the notebook
    with notebook_full_path.open("r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    try:
        # Execute the notebook
        execute_preprocessor.preprocess(notebook, {"metadata": {"path": str(NOTEBOOKS_DIR)}})
    except Exception as e:
        pytest.fail(f"Notebook execution failed for {notebook_path}: {e}")
