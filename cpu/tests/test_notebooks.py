# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: BSD-3-Clause

import os
import pytest
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

NOTEBOOKS_DIR = "cpu/notebooks"

def list_notebooks(directory):
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".ipynb")
    ]

@pytest.mark.parametrize("notebook_path", list_notebooks(NOTEBOOKS_DIR))
def test_notebook_execution(notebook_path):
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=600)

    ep.preprocess(notebook, {"metadata": {"path": os.path.dirname(notebook_path)}})
