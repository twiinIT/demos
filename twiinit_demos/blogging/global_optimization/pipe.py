from math import pi

from cosapp.systems import System
from pyoccad.create import (
    CreateAxis,
    CreateCircle,
    CreateDirection,
    CreateExtrusion,
    CreateLine,
    CreateRevolution,
)
from pyoccad.render import JupyterThreeJSRenderer
from pyoccad.transform import Sweep


class Pipe(System):
    def setup(self):
        self.add_inward("radius", 0.02)
        self.add_inward("thickness", 0.001)
        self.add_inward("length", 1.0)
        self.add_inward("mass_flow", 1.0)
        self.add_inward("g", 9.81)
        self.add_inward("rho", 1000.0)
        self.add_inward("friction", 0.01)
        self.add_inward("density", 3e3)

        self.add_outward("weight")
        self.add_outward("pressure_loss")
        self.add_outward("velocity")

    def compute(self):
        self.weight = (
            pi
            * (self.radius**2 - (self.radius - self.thickness) ** 2)
            * self.length
            * self.density
        )
        self.velocity = self.mass_flow / (self.rho * pi * (self.radius - self.thickness) ** 2)
        self.pressure_loss = (
            self.friction * self.length * self.velocity**2 / (4.0 * self.g * self.radius)
        )

    def _cad_repr_(self):
        l1 = CreateLine.between_2_points((0.5, 0.0, -5.0), (0.45, 0.0, -5.0))
        s1 = CreateRevolution.surface_from_curve(l1, CreateAxis.oz())
        pipe1 = CreateExtrusion.surface(s1, (0.0, 0.0, 10.0))

        r = JupyterThreeJSRenderer(view_size=(1200, 600), background_color="white")
        r.add_shape(pipe1, face_color="darkcyan")
        return r.show()
