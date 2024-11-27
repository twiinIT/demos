# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache-2.0

from math import pi

from cosapp.systems import System
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid
from OCC.Core.Geom import Geom_Plane
from pyoccad.create import (
    CreateAxis,
    CreateCircle,
    CreateCylinder,
    CreateOCCList,
    CreateRotation,
    CreateTopology,
)
from pyoccad.explore import ExploreSubshapes

from ..systems import ParametricBladeGeometry


class RotorGeometry(System):
    """Rotor geometry system."""

    def setup(self):
        self.add_child(
            ParametricBladeGeometry("blade"),
            pulling={
                "tip_radius": "tip_radius",
                "hub_to_tip_ratio": "hub_to_tip_ratio",
                "position": "blade_position",
                "dimension": "blade_dimension",
            },
        )

        self.add_inward("count", 2)
        self.add_inward("thickness", 1e-3, unit="m")
        self.add_outward("geometry", None)

    def compute(self):
        blades = []
        for i in range(self.count):
            trsf = BRepBuilderAPI_Transform(
                self.blade.geometry, CreateRotation.rotation_x(2 * pi / self.count * i)
            )
            blades.append(trsf.Shape())

        x0 = self.blade_position[0]
        e = self.blade_dimension[0]
        th = self.thickness
        circ = CreateCircle.from_radius_and_axis(
            self.hub_to_tip_ratio * self.tip_radius - th,
            CreateAxis.as_axis(((x0, 0.0, 0.0), (1.0, 0.0, 0.0))),
        )
        moyeu = CreateCylinder.solid_from_base_and_height(circ, e)

        faces = ExploreSubshapes.get_faces(moyeu)

        to_remove = []
        for f in faces:
            g = Geom_Plane.DownCast(BRep_Tool.Surface(f))
            if g and g.Location().X() > x0:
                to_remove.append(f)

        to_remove = CreateOCCList.of_shapes(to_remove)

        builder = BRepOffsetAPI_MakeThickSolid()
        builder.MakeThickSolidByJoin(moyeu, to_remove, th, 1e-6)
        hollowed_moyeu = builder.Shape()

        self.geometry = CreateTopology.make_compound(*blades, hollowed_moyeu)
