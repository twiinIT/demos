# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from ..systems import (
    CPU,
    CasingGeometry,
    CPUSystem,
    Fan,
    FanController,
    FanGeometry,
    HeatExchanger,
    ParametricBladeGeometry,
    RotorGeometry,
)

cls_list = [
    ParametricBladeGeometry,
    CPU,
    CPUSystem,
    Fan,
    FanController,
    HeatExchanger,
    CasingGeometry,
    FanGeometry,
    RotorGeometry,
]


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
