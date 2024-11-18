# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache2.0

from cosapp.ports import Port


class Fluid(Port):
    def setup(self):

        self.add_variable("mass_flow", unit="g/s", desc="Mass flow")
        self.add_variable("T", unit="degC", desc="Temperature")
