# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache2.0

from math import cos, radians, sin

import numpy as np
from cosapp.systems import System
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Core.BRepLib import breplib
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.gp import gp_Ax2d, gp_Dir2d, gp_GTrsf2d, gp_Pnt2d
from pyoccad.create import (
    CreateArray1,
    CreateBSpline,
    CreateCurve,
    CreateLine,
    CreatePlane,
    CreateUnsignedCoordSystem,
)
from pyoccad.measure import MeasureCurve
from pyoccad.measure.shape import bounds
from pyoccad.transform import Sweep, Translate


class ParametricBladeGeometry(System):
    """Parametric blade geometry system."""

    def setup(self):
        self.add_inward("inlet_angle", 0.0, unit="deg")
        self.add_inward("exit_angle", 0.0, unit="deg")
        self.add_inward("max_thickness_ratio", 0.03, unit="")
        self.add_inward("max_thickness_position", 0.3, unit="")

        self.add_inward("height_over_chord", 2.0, unit="")
        self.add_inward("swirl", 0.0, unit="")

        self.add_inward("tip_radius", 0.1, unit="m")
        self.add_inward("hub_to_tip_ratio", 0.1, unit="")
        self.add_inward("q_factor", 1.0, unit="")

        self.add_inward("leading_tension", 10, unit="")
        self.add_inward("trailing_tension", 10.0, unit="")

        self.add_inward("stacking_parameter", 0.0, unit="")
        self.add_inward("stacking_angle", 0.0, unit="deg")

        self.add_outward("stagger_angle", 0.0, unit="deg")
        self.add_outward("dimension", np.empty(3), unit="m")
        self.add_outward("position", np.empty(3), unit="m")
        self.add_outward("backbone", None)
        self.add_outward("geometry", None)

    def compute(self):

        hub_radius = self.tip_radius * self.hub_to_tip_ratio
        mean_radius = self.tip_radius * (1.0 + self.hub_to_tip_ratio) / 2.0
        height = self.tip_radius - hub_radius
        chord = height / self.height_over_chord

        # max_thickness = self.max_thickness_ratio * chord
        self.stagger_angle = (radians(self.inlet_angle) + radians(self.exit_angle)) / 2.0

        xi = 0.0
        yi = 0.0
        xe = sin(self.stagger_angle)
        ye = cos(self.stagger_angle)

        tstart = (
            self.leading_tension
            * np.r_[sin(radians(self.inlet_angle)), cos(radians(self.inlet_angle))]
        )
        tend = (
            self.trailing_tension
            * np.r_[sin(radians(self.exit_angle)), cos(radians(self.exit_angle))]
        )
        backbone2d = CreateCurve.as_curve(
            CreateBSpline.from_points_interpolate_with_bounds_control(
                ((xi, yi), (xe, ye)),
                tangents=(tstart, tend),
                tol=1e-6,
                periodic=False,
                directions_only=False,
            )
        )
        self.backbone = CreateCurve.from_2d(backbone2d, CreatePlane.xpy((0.0, 0.0, 0.0)))

        center2d = np.array(
            MeasureCurve.value(
                backbone2d, backbone2d.LastParameter() * self.max_thickness_position
            ).Coord()
        )
        xebb, yebb = center2d
        de = self.max_thickness_ratio
        xemax1 = xebb - de * cos(self.stagger_angle) * 2.0 / 3.0
        yemax1 = yebb + de * sin(self.stagger_angle) * 2.0 / 3.0
        xemax2 = xebb + de * cos(self.stagger_angle) / 3.0
        yemax2 = yebb - de * sin(self.stagger_angle) / 3.0

        center2d2 = np.array(
            MeasureCurve.value(
                backbone2d, backbone2d.LastParameter() * self.stacking_parameter
            ).Coord()
        )
        c1 = CreateBSpline.from_points_interpolate_with_bounds_control(
            (
                np.array(((xe, ye), (xemax1, yemax1), (xi, yi), (xemax2, yemax2), (xe, ye)))
                - center2d2
            ).tolist(),
            tangents=(-tend, tend),
            tol=1e-6,
            periodic=False,
            directions_only=False,
        )

        def scale_2d_profile(curve, f, se):
            gtrsf1 = gp_GTrsf2d()
            gtrsf1.SetAffinity(gp_Ax2d(gp_Pnt2d(), gp_Dir2d(1.0, 0.0)), f)
            gtrsf2 = gp_GTrsf2d()
            gtrsf2.SetAffinity(gp_Ax2d(gp_Pnt2d(), gp_Dir2d(0.0, 1.0)), se)

            arr = CreateArray1.of_points([p for p in curve.Poles()])
            for i in range(1, arr.Length() + 1):
                p = arr.Value(i)
                p.SetXY(gtrsf2.Transformed(gtrsf1.Transformed(p.XY())))
                curve.SetPole(i, p)

        scale_2d_profile(c1, chord, chord / mean_radius)

        cyl1 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), hub_radius)
        proj1 = BRepBuilderAPI_MakeEdge(c1, cyl1).Shape()
        breplib.BuildCurve3d(proj1)

        cyl2 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), mean_radius)
        proj2 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(c1, (-radians(self.swirl) / 2.0, 0.0), inplace=False), cyl2
        ).Shape()
        breplib.BuildCurve3d(proj2)

        cyl3 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), self.tip_radius)
        proj3 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(c1, (-radians(self.swirl), 0.0), inplace=False), cyl3
        ).Shape()
        breplib.BuildCurve3d(proj3)

        segment = CreateLine.between_2_points(
            BRep_Tool.Curve(proj1)[0].Value(0.0), BRep_Tool.Curve(proj3)[0].Value(0.0)
        )
        sw = Sweep.profiles_along_path((proj1, proj2, proj3), segment, build_solid=True)

        bbox = np.array(bounds(proj1))
        # rmin_box = max(sqrt(bbox[1] ** 2 + bbox[2] ** 2), sqrt(bbox[4] ** 2 + bbox[5] ** 2))
        xmin_box = bbox[0]
        # hx_box = bbox[3] - bbox[0]

        self.position = np.r_[xmin_box, 0.0, 0.0]
        self.dimension = bbox[3:] - bbox[:3]

        self.geometry = sw
        # geometry = CreateTopology.make_edge(self.backbone)
        # self.geometry = CreateTopology.make_compound(proj1, proj2, proj3)
