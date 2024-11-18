# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache2.0

from math import cos, pi

import numpy as np
from cosapp.systems import System
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform,
)
from OCC.Core.BRepLib import breplib
from OCC.Core.Geom import Geom_CylindricalSurface
from pyoccad.create import (
    CreateAxis,
    CreateCircle,
    CreateCylinder,
    CreateExtrusion,
    CreateLine,
    CreatePlane,
    CreatePoint,
    CreateRotation,
    CreateTopology,
    CreateUnsignedCoordSystem,
    CreateVector,
    CreateWire,
)
from pyoccad.transform import Sweep


class CasingGeometry(System):
    """Casing geometry system."""

    def setup(self):
        self.add_inward("blade_tip_radius", 0.1, unit="m")
        self.add_inward("blade_hub_to_tip_ratio", 0.3, unit="")

        self.add_inward("blade_dimension", np.empty(3), unit="m")
        self.add_inward("blade_position", np.empty(3), unit="m")

        self.add_inward("struts_width_ratio", 0.05, unit="")
        self.add_inward("struts_min_width", 0.005, unit="m")
        self.add_inward("struts_thickness_ratio", 0.03, unit="")
        self.add_inward("struts_min_thickness", 0.002, unit="m")
        self.add_inward("struts_clearance_ratio", 0.05, unit="")
        self.add_inward("struts_min_clearance", 0.005, unit="m")

        self.add_inward("thickness_ratio", 0.05, unit="")
        self.add_inward("min_thickness", 0.008)

        self.add_inward("clearance_ratio", 0.01, unit="")
        self.add_inward("min_clearance", 0.002, unit="m")

        self.add_outward("width", 0.1, unit="m")
        self.add_outward("height", 0.1, unit="m")
        self.add_outward("geometry", None)

    def compute(self):
        clearance = max(self.clearance_ratio * self.blade_tip_radius, self.min_clearance)
        thickness = max(self.thickness_ratio * self.blade_tip_radius, self.min_thickness)
        size = self.width = self.height = self.blade_tip_radius + thickness + clearance

        struts_width = max(self.struts_width_ratio * self.blade_tip_radius, self.struts_min_width)
        struts_thickness = max(
            self.struts_thickness_ratio * self.blade_tip_radius, self.struts_min_thickness
        )
        struts_clearance = max(
            self.struts_clearance_ratio * self.blade_tip_radius, self.struts_min_clearance
        )

        x0 = self.blade_position[0]
        e = self.blade_dimension[0] + struts_clearance + struts_thickness
        st = sw = size

        pt1 = CreatePoint.as_point((x0 + e * 3.0 / 8, sw, st))
        pt2 = CreatePoint.as_point((x0 + e * 3.0 / 8, -sw, st))
        pt3 = CreatePoint.as_point((x0 + e * 3.0 / 8, -sw, -st))
        pt4 = CreatePoint.as_point((x0 + e * 3.0 / 8, sw, -st))
        w1 = CreateWire.from_points((pt1, pt2, pt3, pt4), auto_close=True)

        c = CreateCircle.from_radius_center_normal(
            self.blade_tip_radius + clearance, (x0, 0.0, 0.0), CreateVector.ox()
        )
        w2 = CreateWire.from_element(c)

        c2 = CreateCircle.from_radius_center_normal(
            self.blade_tip_radius + clearance + 0.002, (x0, 0.0, 0.0), CreateVector.ox()
        )
        w3 = CreateWire.from_element(c2)

        f = face_from_wires(CreatePlane.ypz((x0, 0.0, 0.0)), w2.Reversed(), w3)
        casing = CreateExtrusion.surface(f, (e, 0.0, 0.0))

        c4 = CreateCircle.from_radius_center_normal(
            self.blade_tip_radius + clearance + 0.002,
            (x0 + e * 3.0 / 8.0, 0.0, 0.0),
            CreateVector.ox(),
        )
        w4 = CreateWire.from_element(c4)

        hole = CreateCircle.from_radius_center_normal(
            0.004, (x0 + e * 3.0 / 8, sw - 0.015, st - 0.015), CreateVector.ox()
        )
        wh = CreateWire.from_element(hole)
        holes = []
        for i in range(4):
            trsf = BRepBuilderAPI_Transform(wh, CreateRotation.rotation_x(pi / 2.0 * i))
            holes.append(trsf.Shape().Reversed())

        f2 = face_from_wires(
            CreatePlane.ypz((x0 + e * 3.0 / 8.0, 0.0, 0.0)), w1, w4.Reversed(), *holes
        )
        casing2 = CreateExtrusion.surface(f2, (e / 4.0, 0.0, 0.0))

        x0 += e - struts_thickness
        st = struts_thickness
        sw = struts_width

        def rectangle_on_cylinder(pos, dims, radius):
            x, y = pos
            sw, st = dims
            sw /= radius
            pt1 = CreatePoint.as_point((x + sw / 2.0, y + st))
            pt2 = CreatePoint.as_point((x - sw / 2.0, y + st))
            pt3 = CreatePoint.as_point((x - sw / 2.0, y))
            pt4 = CreatePoint.as_point((x + sw / 2.0, y))

            l1 = CreateLine.between_2_points(pt1, pt2)
            l2 = CreateLine.between_2_points(pt2, pt3)
            l3 = CreateLine.between_2_points(pt3, pt4)
            l4 = CreateLine.between_2_points(pt4, pt1)

            cyl1 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), radius)
            proj1 = BRepBuilderAPI_MakeEdge(l1, cyl1).Shape()
            breplib.BuildCurve3d(proj1)
            proj2 = BRepBuilderAPI_MakeEdge(l2, cyl1).Shape()
            breplib.BuildCurve3d(proj2)
            proj3 = BRepBuilderAPI_MakeEdge(l3, cyl1).Shape()
            breplib.BuildCurve3d(proj3)
            proj4 = BRepBuilderAPI_MakeEdge(l4, cyl1).Shape()
            breplib.BuildCurve3d(proj4)

            w = CreateWire.from_elements((proj1, proj2, proj3, proj4))

            return w

        hub_radius = self.blade_hub_to_tip_ratio * self.blade_tip_radius
        w1 = rectangle_on_cylinder((pi / 4.0, x0), (sw, st), self.blade_tip_radius + clearance)
        w2 = rectangle_on_cylinder((pi / 4.0, x0), (sw, st), hub_radius)

        istart = hub_radius * cos(pi / 4.0)
        iend = (self.blade_tip_radius + clearance) * cos(pi / 4.0)
        strut = CreateLine.between_2_points((x0, istart, istart), (x0, iend, iend))
        strut = Sweep.profiles_along_path((w1, w2), strut)

        struts = []
        for i in range(4):
            trsf = BRepBuilderAPI_Transform(strut, CreateRotation.rotation_x(pi / 2.0 * i))
            struts.append(trsf.Shape())

        circ = CreateCircle.from_radius_and_axis(
            hub_radius, CreateAxis.as_axis(((x0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        )
        motor_plate = CreateCylinder.solid_from_base_and_height(circ, struts_thickness)

        self.geometry = CreateTopology.make_compound(casing, casing2, *struts, motor_plate)


def face_from_wires(plane, *wires):
    """Create a face from a plane and wires."""
    builder = BRepBuilderAPI_MakeFace(plane)
    for w in wires:
        builder.Add(w)

    return builder.Shape()
