# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache-2.0

from cosapp.ports import Port


class GeomPort(Port):
    """Geometry port."""

    def setup(self):
        self.add_variable("visible", True)
        self.add_variable("shape", None)
