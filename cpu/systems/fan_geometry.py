# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache-2.0

from cosapp.systems import System
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from pyoccad.create import CreateScaling, CreateTopology

from ..ports import GeomPort
from ..systems import CasingGeometry, RotorGeometry


class FanGeometry(System):
    """Fan geometry system."""

    def setup(self):
        rotor = self.add_child(RotorGeometry("rotor"), pulling=["tip_radius", "hub_to_tip_ratio"])
        casing = self.add_child(CasingGeometry("casing"))

        self.connect(
            rotor.inwards,
            casing.inwards,
            {"tip_radius": "blade_tip_radius", "hub_to_tip_ratio": "blade_hub_to_tip_ratio"},
        )
        self.connect(rotor.outwards, casing.inwards, ["blade_position", "blade_dimension"])

        self.add_inward("factor", 1.0, unit="")

        self.add_output(GeomPort, "geometry")

    def compute(self):
        geom = CreateTopology.make_compound(self.rotor.geometry, self.casing.geometry)
        self.geometry.shape = BRepBuilderAPI_Transform(
            geom, CreateScaling.from_factor(self.factor)
        ).Shape()
