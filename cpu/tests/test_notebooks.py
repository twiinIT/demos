# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: BSD-3-Clause


from pathlib import Path
import glob
import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"


list_nb = [file.name for file in NOTEBOOKS_DIR.glob("*ipynb")]
list_nb = sorted(list_nb, key=lambda n: int(n.split("-")[0]))


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
