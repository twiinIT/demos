import numpy as np

from cosapp.systems import System

from pythonocc_helpers.create import CreateCircle, CreateExtrusion, CreatePlane, CreateLine, CreateRevolution, CreateAxis, CreateWire, CreateTopology, CreateBox
from pythonocc_helpers.transform import Sweep, Translate, Scale, BooleanOperation
import pythonocc_helpers.measure.shape as measure_shape

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace

#from ..ports.fluid import Fluid


def face_from_wires(plane, *wires):
    builder = BRepBuilderAPI_MakeFace(plane)  
    for w in wires:
        builder.Add(CreateWire.from_element(w))
        
    return builder.Shape()


class PipeGeometry(System):

    def setup(self):
        self.add_inward("length", 1., unit="m", desc="Pipe length")
        self.add_inward("diameter", 0.1, unit="m", desc="Pipe diameter")
        self.add_inward("thickness", 1e-3, unit="m", desc="Pipe thickness")

        self.add_outward("shape", None, desc="Shape")

    def compute(self):
        inner_radius = self.diameter / 2.
        c1 = CreateCircle.from_radius_center_normal(inner_radius, (0., 0., 0.), (1., 0., 0.))
        c2 = CreateCircle.from_radius_center_normal(inner_radius - self.thickness, (0., 0., 0.), (1., 0., 0.))
        s = face_from_wires(CreatePlane.yoz(), c1, c2.Reversed())
        self.shape = CreateExtrusion.surface(s, (self.length, 0., 0.))

        
class HeatExchangerGeometry(System):

    def setup(self):
        
        self.add_child(PipeGeometry("pipe"), pulling=["length", "diameter", "thickness"])

        self.add_inward("branch_count", 1, unit="", desc="Branch count")
        self.add_inward("branch_spacing", 0.1, unit="m", desc="Distance between branches")
        self.add_inward("depth", 2.5, unit="m", desc="Depth")

        self.add_outward("shape", None, desc="Shape")

    def compute(self):
        assert self.branch_spacing >= self.diameter

        pipe_shape = self.pipe.shape
        pipes = [Translate.from_vector(pipe_shape, (0., -self.depth, self.branch_spacing * (i - (self.branch_count - 1) / 2)), inplace=False) for i in range(self.branch_count)]

        self.shape = CreateTopology.make_compound(*pipes)


class PipeMaterial(System):

    def setup(self):

        self.add_inward("lambda", unit="J/K/m**2", desc="Pipe diameter")
        self.add_inward("density", unit="kg/m**3", desc="Pipe density")


class Pipe(System):

    def setup(self):
        self.add_child(PipeMaterial("material"))
        self.add_child(PipeGeometry("geometry"))

        #self.add_input("fl_in", Fluid)
        #self.add_output("fl_out", Fluid)


class HeatExchanger(System):

    def setup(self):

        self.add_child(PipeMaterial("material"))
        self.add_child(HeatExchangerGeometry("geometry"), pulling={"shape": "geom"})

        #self.add_input("fl_in", Fluid)
        #self.add_output("fl_out", Fluid)

        self.add_inward("ground_temperature", 273.15, unit="K", desc="Ground temperature")

    def compute(self):
        pass


class GroundMaterial(System):

    def setup(self):
        self.add_inward("lambda", 1.5, unit="W/m/K", desc="Heat conductivity")
        self.add_inward("density", 1500., unit="kg/m**3", desc="Density")
        self.add_inward("cp", unit="J/(kg*K)", desc="Heat capacity")


class Ground(System):

    def setup(self):
        self.add_child(GroundMaterial("material"))

        self.add_inward("exchanger_geometry", None, desc="Exchanger geometry")
        self.add_inward("outside_temp", unit="K", desc="Outside temperature")
        self.add_inward("h", unit="J/K/m**2", desc="Heat diffusion coefficient")
    
    def compute(self):
        pass

    def _cad_repr_(self, factor=1.):
        exchanger_bbox = np.array(measure_shape.bounds(self.exchanger_geometry, optimal=False, use_triangulation=False))
        dims = exchanger_bbox[3:] - exchanger_bbox[:3]
        center = dims / 2. + exchanger_bbox[:3]

        dims[1] = -exchanger_bbox[1]
        center[1] = exchanger_bbox[1] / 2.

        bbox = CreateBox.from_dimensions_and_center(dims, center)
        center[1] = 0.
        return Scale.from_factor_and_center(bbox, factor, center, inplace=False)


class Atmosphere(System):

    def setup(self):
        self.add_inward("temperature", unit="K", desc="Air temperature")
        self.add_inward("heat_flow", unit="W", desc="Heat flow")


class Outside(System):

    def setup(self):
        self.add_inward("temperature", unit="K", desc="Air temperature")
        self.add_inward("heat_flow", unit="W", desc="Heat flow")


class EarthToAirExchanger(System):

    def setup(self):
        self.add_child(HeatExchanger("exchanger"))
        self.add_child(Ground("ground"))

        self.connect(self.exchanger.outwards, self.ground.inwards, {"geom": "exchanger_geometry"})
