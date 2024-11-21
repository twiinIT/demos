# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache-2.0

from cosapp.systems import System


class FanController(System):
    """Define tension for fan from the level of CPU temperature."""

    def setup(self):
        # inputs
        self.add_inward("T_cpu", unit="degC", desc="CPU temperature")
        self.add_inward(
            "low_threshold", 40.0, unit="degC", desc="Low to medium temperature threshold"
        )
        self.add_inward(
            "high_threshold", 60.0, unit="degC", desc="Medium to high temperature threshold"
        )
        self.add_inward("low_tension", 0.0, unit="V", desc="Output low tension")
        self.add_inward("medium_tension", 6.0, unit="V", desc="Output medium tension")
        self.add_inward("max_tension", 12.0, unit="V", desc="Output max tension")

        # outputs
        self.add_outward("tension", 0.0, unit="V", desc="Output tension")

    def compute(self):
        if self.T_cpu <= self.low_threshold:
            self.tension = self.low_tension
        elif self.T_cpu <= self.high_threshold:
            self.tension = self.medium_tension
        else:
            self.tension = self.max_tension
