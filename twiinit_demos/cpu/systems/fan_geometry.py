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
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid
from OCC.Core.Geom import Geom_CylindricalSurface, Geom_Plane
from OCC.Core.gp import gp_Ax2d, gp_Dir2d, gp_GTrsf2d, gp_Pnt2d
from pyoccad.create import (
    CreateArray1,
    CreateAxis,
    CreateBSpline,
    CreateCircle,
    CreateCurve,
    CreateCylinder,
    CreateExtrusion,
    CreateLine,
    CreateOCCList,
    CreatePlane,
    CreatePoint,
    CreateRotation,
    CreateScaling,
    CreateTopology,
    CreateUnsignedCoordSystem,
    CreateVector,
    CreateWire,
)
from pyoccad.explore import ExploreSubshapes
from pyoccad.measure import MeasureCurve
from pyoccad.measure.shape import bounds
from pyoccad.transform import Sweep, Translate

from ..ports.geom import GeomPort


def face_from_wires(plane, *wires):
    builder = BRepBuilderAPI_MakeFace(plane)
    for w in wires:
        builder.Add(w)

    return builder.Shape()


class ParametricBladeGeometry(System):
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

        max_thickness = self.max_thickness_ratio * chord
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
                tangents_indices=[0, -1],
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
            tangents_indices=[0, -1],
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
        breplib_BuildCurve3d(proj1)

        cyl2 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), mean_radius)
        proj2 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(c1, (-radians(self.swirl) / 2.0, 0.0), inplace=False), cyl2
        ).Shape()
        breplib_BuildCurve3d(proj2)

        cyl3 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), self.tip_radius)
        proj3 = BRepBuilderAPI_MakeEdge(
            Translate.from_vector(c1, (-radians(self.swirl), 0.0), inplace=False), cyl3
        ).Shape()
        breplib_BuildCurve3d(proj3)

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
        geometry = CreateTopology.make_edge(self.backbone)
        # self.geometry = CreateTopology.make_compound(proj1, proj2, proj3)


class CasingGeometry(System):
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
        L = l = size

        pt1 = CreatePoint.as_point((x0 + e * 3.0 / 8, l, L))
        pt2 = CreatePoint.as_point((x0 + e * 3.0 / 8, -l, L))
        pt3 = CreatePoint.as_point((x0 + e * 3.0 / 8, -l, -L))
        pt4 = CreatePoint.as_point((x0 + e * 3.0 / 8, l, -L))
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
            0.004, (x0 + e * 3.0 / 8, l - 0.015, L - 0.015), CreateVector.ox()
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
        L = struts_thickness
        l = struts_width

        def rectangle_on_cylinder(pos, dims, radius):
            x, y = pos
            l, L = dims
            l /= radius
            pt1 = CreatePoint.as_point((x + l / 2.0, y + L))
            pt2 = CreatePoint.as_point((x - l / 2.0, y + L))
            pt3 = CreatePoint.as_point((x - l / 2.0, y))
            pt4 = CreatePoint.as_point((x + l / 2.0, y))

            l1 = CreateLine.between_2_points(pt1, pt2)
            l2 = CreateLine.between_2_points(pt2, pt3)
            l3 = CreateLine.between_2_points(pt3, pt4)
            l4 = CreateLine.between_2_points(pt4, pt1)

            from OCC.Core.BRepLib import breplib_BuildCurve3d, breplib_BuildCurves3d

            cyl1 = Geom_CylindricalSurface(CreateUnsignedCoordSystem.ox(), radius)
            proj1 = BRepBuilderAPI_MakeEdge(l1, cyl1).Shape()
            breplib_BuildCurve3d(proj1)
            proj2 = BRepBuilderAPI_MakeEdge(l2, cyl1).Shape()
            breplib_BuildCurve3d(proj2)
            proj3 = BRepBuilderAPI_MakeEdge(l3, cyl1).Shape()
            breplib_BuildCurve3d(proj3)
            proj4 = BRepBuilderAPI_MakeEdge(l4, cyl1).Shape()
            breplib_BuildCurve3d(proj4)

            w = CreateWire.from_elements((proj1, proj2, proj3, proj4))

            return w

        hub_radius = self.blade_hub_to_tip_ratio * self.blade_tip_radius
        w1 = rectangle_on_cylinder((pi / 4.0, x0), (l, L), self.blade_tip_radius + clearance)
        w2 = rectangle_on_cylinder((pi / 4.0, x0), (l, L), hub_radius)

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


class RotorGeometry(System):
    def setup(self):
        blade = self.add_child(
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


class FanGeometry(System):
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
