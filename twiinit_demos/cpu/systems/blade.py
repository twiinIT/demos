from math import cos, pi, radians, sin, sqrt

import numpy as np
from cosapp.systems import System
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform,
)
from OCC.Core.BRepLib import breplib_BuildCurve3d
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.gp import gp_Ax2d, gp_Dir2d, gp_GTrsf2d, gp_Pnt2d
from pyoccad.create import (
    CreateArray1,
    CreateBSpline,
    CreateCurve,
    CreateEdge,
    CreateLine,
    CreateRotation,
    CreateTopology,
    CreateUnsignedCoordSystem,
    CreateVector,
)
from pyoccad.measure import MeasureCurve
from pyoccad.measure.shape import bounds
from pyoccad.transform import Move, Sweep, Translate


def face_from_wires(plane, *wires):
    builder = BRepBuilderAPI_MakeFace(plane)
    for w in wires:
        builder.Add(w)

    return builder.Shape()


class ParametricBladeGeometry(System):
    def setup(self):
        # backbone inputs
        self.add_inward("inlet_angle", 0.0, unit="deg")
        self.add_inward("exit_angle", 0.0, unit="deg")

        self.add_inward("leading_tension", 10, unit="")
        self.add_inward("trailing_tension", 10.0, unit="")

        # profile inputs
        self.add_inward("max_thickness_ratio", 0.03, unit="")
        self.add_inward("max_thickness_position", 0.3, unit="")
        self.add_inward("max_thickness_th_pos", 0.5, unit="")

        self.add_inward("height_over_chord", 2.0, unit="")
        self.add_inward("swirl", 0.0, unit="")

        self.add_inward("tip_delta_stagger", 0.0, unit="deg")
        self.add_inward("hub_delta_stagger", 0.0, unit="deg")

        self.add_inward("tip_radius", 0.1, unit="m")
        self.add_inward("hub_to_tip_ratio", 0.1, unit="")
        self.add_inward("q_factor", 1.0, unit="")

        self.add_inward("stacking_parameter", 0.0, unit="")
        self.add_inward("stacking_angle", 0.0, unit="deg")

        self.add_outward("dimension", np.empty(3), unit="m")
        self.add_outward("position", np.empty(3), unit="m")

        self.add_outward("stagger_angle", 0.0, unit="rad")

        self.add_outward("backbone", None)
        self.add_outward("backbone2d", None)
        self.add_outward("backbone2d_unscaled", None)
        self.add_outward("geometry", None)

    def compute_backbone(self):
        self.stagger_angle = stagger_angle = (
            radians(self.inlet_angle) + radians(self.exit_angle)
        ) / 2.0

        xi = 0.0
        yi = 0.0
        xe = sin(stagger_angle)
        ye = cos(stagger_angle)

        tstart = (
            self.leading_tension
            * np.r_[sin(radians(self.inlet_angle)), cos(radians(self.inlet_angle))]
        )
        tend = (
            self.trailing_tension
            * np.r_[sin(radians(self.exit_angle)), cos(radians(self.exit_angle))]
        )
        self.backbone2d_unscaled = CreateCurve.as_curve(
            CreateBSpline.from_points_interpolate_with_bounds_control(
                ((xi, yi), (xe, ye)),
                tangents=(tstart, tend),
                tol=1e-6,
                periodic=False,
                directions_only=False,
            )
        )

    def compute(self):
        self.compute_backbone()

        hub_radius = self.tip_radius * self.hub_to_tip_ratio
        mean_radius = self.tip_radius * (1.0 + self.hub_to_tip_ratio) / 2.0
        height = self.tip_radius - hub_radius
        chord = height / self.height_over_chord

        xi = 0.0
        yi = 0.0
        xe = sin(self.stagger_angle)
        ye = cos(self.stagger_angle)

        bb2d = self.backbone2d_unscaled

        tend = MeasureCurve.derivatives(bb2d, bb2d.LastParameter(), 1)[1]

        center2d = np.array(
            MeasureCurve.value(bb2d, bb2d.LastParameter() * self.max_thickness_position).Coord()
        )
        xebb, yebb = center2d
        de = self.max_thickness_ratio
        xemax1 = xebb - de * cos(self.stagger_angle) * self.max_thickness_th_pos
        yemax1 = yebb + de * sin(self.stagger_angle) * self.max_thickness_th_pos
        xemax2 = xebb + de * cos(self.stagger_angle) * (1.0 - self.max_thickness_th_pos)
        yemax2 = yebb - de * sin(self.stagger_angle) * (1.0 - self.max_thickness_th_pos)

        center2d2 = np.array(
            MeasureCurve.value(bb2d, bb2d.LastParameter() * self.stacking_parameter).Coord()
        )
        c1 = CreateBSpline.from_points_interpolate_with_bounds_control(
            (
                np.array(((xe, ye), (xemax1, yemax1), (xi, yi), (xemax2, yemax2), (xe, ye)))
                - center2d2
            ).tolist(),
            tangents=(-tend, tend),
            tangents_indices=(0, -1),
            tol=1e-6,
            periodic=False,
            directions_only=False,
        )

        # c1 = CreateEdge

        def scale_2d_profile(curve, f, se, inplace=True):
            gtrsf1 = gp_GTrsf2d()
            gtrsf1.SetAffinity(gp_Ax2d(gp_Pnt2d(), gp_Dir2d(1.0, 0.0)), f)
            gtrsf2 = gp_GTrsf2d()
            gtrsf2.SetAffinity(gp_Ax2d(gp_Pnt2d(), gp_Dir2d(0.0, 1.0)), se)

            new_curve = curve if inplace else type(curve).DownCast(curve.Copy())
            arr = CreateArray1.of_points([p for p in new_curve.Poles()])

            for i in range(1, arr.Length() + 1):
                p = arr.Value(i)
                p.SetXY(gtrsf2.Transformed(gtrsf1.Transformed(p.XY())))
                new_curve.SetPole(i, p)

            return new_curve

        scale_2d_profile(c1, chord, chord / mean_radius)

        if self.stagger_angle:
            stagger_sign = self.stagger_angle / abs(self.stagger_angle)
        else:
            stagger_sign = 1.0

        rot = CreateRotation.rotation_z_2d_deg(stagger_sign * self.hub_delta_stagger)
        hub_profile = Move.using_transformation(c1, rot, inplace=False)
        cyl1 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), hub_radius)
        proj1 = BRepBuilderAPI_MakeEdge(hub_profile, cyl1).Shape()
        breplib_BuildCurve3d(proj1)

        cyl2 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), mean_radius)
        proj2 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(c1, (-radians(self.swirl) / 2.0, 0.0), inplace=False), cyl2
        ).Shape()
        breplib_BuildCurve3d(proj2)

        rot = CreateRotation.rotation_z_2d_deg(stagger_sign * self.tip_delta_stagger)
        tip_profile = Move.using_transformation(c1, rot, inplace=False)
        cyl3 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), self.tip_radius)
        proj3 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(tip_profile, (-radians(self.swirl), 0.0), inplace=False), cyl3
        ).Shape()
        breplib_BuildCurve3d(proj3)

        Translate.from_vector(bb2d, CreateVector.as_vector(-center2d2))
        bb2d_scaled = scale_2d_profile(bb2d, chord, chord / mean_radius, inplace=False)
        self.backbone = BRepBuilderAPI_MakeEdge(bb2d_scaled, cyl2).Shape()
        breplib_BuildCurve3d(self.backbone)

        segment = CreateLine.between_2_points(
            BRep_Tool.Curve(proj1)[0].Value(0.0), BRep_Tool.Curve(proj3)[0].Value(0.0)
        )
        sw = Sweep.profiles_along_path((proj1, proj2, proj3), segment, build_solid=True)

        bbox = np.array(bounds(proj1))
        rmin_box = max(sqrt(bbox[1] ** 2 + bbox[2] ** 2), sqrt(bbox[4] ** 2 + bbox[5] ** 2))
        xmin_box = bbox[0]
        hx_box = bbox[3] - bbox[0]

        self.position = np.r_[xmin_box, 0.0, 0.0]
        self.dimension = bbox[3:] - bbox[:3]

        self.geometry = sw
        # geometry = CreateTopology.make_edge(self.backbone)
        # self.geometry = CreateTopology.make_compound(proj1, proj2, proj3)


class RotorGeometry(System):
    def setup(self):
        blade = self.add_child(
            ParametricBladeGeometry("blade"),
            pulling={
                "tip_radius": "tip_radius",
                "hub_to_tip_ratio": "hub_to_tip_ratio",
                "position": "blade_position",
                "dimension": "blade_dimension",
                "inlet_angle": "inlet_angle",
                "exit_angle": "exit_angle",
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

        self.geometry = CreateTopology.make_compound(*blades)


class ParametricBladeGeometryOld(System):
    def setup(self):
        # backbone inputs
        self.add_inward("inlet_angle", 0.0, unit="deg")
        self.add_inward("exit_angle", 0.0, unit="deg")

        self.add_inward("leading_tension", 10, unit="")
        self.add_inward("trailing_tension", 10.0, unit="")

        # profile inputs
        self.add_inward("max_thickness_ratio", 0.03, unit="")
        self.add_inward("max_thickness_position", 0.3, unit="")
        self.add_inward("max_thickness_th_pos", 0.5, unit="")

        self.add_inward("height_over_chord", 2.0, unit="")
        self.add_inward("swirl", 0.0, unit="")

        self.add_inward("tip_delta_stagger", 0.0, unit="deg")
        self.add_inward("hub_delta_stagger", 0.0, unit="deg")

        self.add_inward("tip_radius", 0.1, unit="m")
        self.add_inward("hub_to_tip_ratio", 0.1, unit="")
        self.add_inward("q_factor", 1.0, unit="")

        self.add_inward("stacking_parameter", 0.0, unit="")
        self.add_inward("stacking_angle", 0.0, unit="deg")

        self.add_outward("dimension", np.empty(3), unit="m")
        self.add_outward("position", np.empty(3), unit="m")

        self.add_outward("stagger_angle", 0.0, unit="rad")

        self.add_outward("backbone", None)
        self.add_outward("backbone2d", None)
        self.add_outward("backbone2d_unscaled", None)
        self.add_outward("geometry", None)

    def compute_backbone(self):
        self.stagger_angle = stagger_angle = (
            radians(self.inlet_angle) + radians(self.exit_angle)
        ) / 2.0

        xi = 0.0
        yi = 0.0
        xe = sin(stagger_angle)
        ye = cos(stagger_angle)

        tstart = (
            self.leading_tension
            * np.r_[sin(radians(self.inlet_angle)), cos(radians(self.inlet_angle))]
        )
        tend = (
            self.trailing_tension
            * np.r_[sin(radians(self.exit_angle)), cos(radians(self.exit_angle))]
        )
        self.backbone2d_unscaled = CreateCurve.as_curve(
            CreateBSpline.from_points_interpolate_with_bounds_control(
                ((xi, yi), (xe, ye)),
                tangents=(tstart, tend),
                tol=1e-6,
                periodic=False,
                directions_only=False,
            )
        )

    def compute(self):
        self.compute_backbone()

        hub_radius = self.tip_radius * self.hub_to_tip_ratio
        mean_radius = self.tip_radius * (1.0 + self.hub_to_tip_ratio) / 2.0
        height = self.tip_radius - hub_radius
        chord = height / self.height_over_chord

        xi = 0.0
        yi = 0.0
        xe = sin(self.stagger_angle)
        ye = cos(self.stagger_angle)

        bb2d = self.backbone2d_unscaled

        tend = MeasureCurve.derivatives(bb2d, bb2d.LastParameter(), 1)[1]

        center2d = np.array(
            MeasureCurve.value(bb2d, bb2d.LastParameter() * self.max_thickness_position).Coord()
        )
        xebb, yebb = center2d
        de = self.max_thickness_ratio
        xemax1 = xebb - de * cos(self.stagger_angle) * self.max_thickness_th_pos
        yemax1 = yebb + de * sin(self.stagger_angle) * self.max_thickness_th_pos
        xemax2 = xebb + de * cos(self.stagger_angle) * (1.0 - self.max_thickness_th_pos)
        yemax2 = yebb - de * sin(self.stagger_angle) * (1.0 - self.max_thickness_th_pos)

        center2d2 = np.array(
            MeasureCurve.value(bb2d, bb2d.LastParameter() * self.stacking_parameter).Coord()
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

        def scale_2d_profile(curve, f, se, inplace=True):
            gtrsf1 = gp_GTrsf2d()
            gtrsf1.SetAffinity(gp_Ax2d(gp_Pnt2d(), gp_Dir2d(1.0, 0.0)), f)
            gtrsf2 = gp_GTrsf2d()
            gtrsf2.SetAffinity(gp_Ax2d(gp_Pnt2d(), gp_Dir2d(0.0, 1.0)), se)

            new_curve = curve if inplace else type(curve).DownCast(curve.Copy())
            arr = CreateArray1.of_points([p for p in new_curve.Poles()])

            for i in range(1, arr.Length() + 1):
                p = arr.Value(i)
                p.SetXY(gtrsf2.Transformed(gtrsf1.Transformed(p.XY())))
                new_curve.SetPole(i, p)

            return new_curve

        scale_2d_profile(c1, chord, chord / mean_radius)

        if self.stagger_angle:
            stagger_sign = self.stagger_angle / abs(self.stagger_angle)
        else:
            stagger_sign = 1.0

        rot = CreateRotation.rotation_z_2d_deg(stagger_sign * self.hub_delta_stagger)
        hub_profile = Move.using_transformation(c1, rot, inplace=False)
        cyl1 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), hub_radius)
        proj1 = BRepBuilderAPI_MakeEdge(hub_profile, cyl1).Shape()
        breplib_BuildCurve3d(proj1)

        cyl2 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), mean_radius)
        proj2 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(c1, (-radians(self.swirl) / 2.0, 0.0), inplace=False), cyl2
        ).Shape()
        breplib_BuildCurve3d(proj2)

        rot = CreateRotation.rotation_z_2d_deg(stagger_sign * self.tip_delta_stagger)
        tip_profile = Move.using_transformation(c1, rot, inplace=False)
        cyl3 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), self.tip_radius)
        proj3 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(tip_profile, (-radians(self.swirl), 0.0), inplace=False), cyl3
        ).Shape()
        breplib_BuildCurve3d(proj3)

        Translate.from_vector(bb2d, CreateVector.as_vector(-center2d2))
        bb2d_scaled = scale_2d_profile(bb2d, chord, chord / mean_radius, inplace=False)
        self.backbone = BRepBuilderAPI_MakeEdge(bb2d_scaled, cyl2).Shape()
        breplib_BuildCurve3d(self.backbone)

        segment = CreateLine.between_2_points(
            BRep_Tool.Curve(proj1)[0].Value(0.0), BRep_Tool.Curve(proj3)[0].Value(0.0)
        )
        sw = Sweep.profiles_along_path((proj1, proj2, proj3), segment, build_solid=True)

        bbox = np.array(bounds(proj1))
        rmin_box = max(sqrt(bbox[1] ** 2 + bbox[2] ** 2), sqrt(bbox[4] ** 2 + bbox[5] ** 2))
        xmin_box = bbox[0]
        hx_box = bbox[3] - bbox[0]

        self.position = np.r_[xmin_box, 0.0, 0.0]
        self.dimension = bbox[3:] - bbox[:3]

        self.geometry = sw
        # geometry = CreateTopology.make_edge(self.backbone)
        # self.geometry = CreateTopology.make_compound(proj1, proj2, proj3)
