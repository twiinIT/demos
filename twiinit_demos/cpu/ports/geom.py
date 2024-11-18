# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache2.0

from cosapp.ports import Port


class GeomPort(Port):
    def setup(self):
        self.add_variable("visible", True)
        self.add_variable("shape", None)
