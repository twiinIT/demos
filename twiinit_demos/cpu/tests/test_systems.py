# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: BSD-3-Clause

import pytest
from ..systems import CPU, CPUSystem, Fan, FanController, HeatExchanger

cls_list = [CPU, CPUSystem, Fan, FanController, HeatExchanger]

@pytest.mark.parametrize("cls", cls_list)
class TestSystems:
    """Define generic tests for cosapp systems."""

    def test_setup(self, cls):
        print("Class name:", cls.__name__)
        cls("sys")
        assert True

    def test_once(self, cls):
        print("Class name:", cls.__name__)
        sys = cls("sys")
        sys.run_once()

        assert True