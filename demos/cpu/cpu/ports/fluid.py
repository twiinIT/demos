from cosapp.ports import Port


class Fluid(Port):
    def setup(self):

        self.add_variable("mass_flow", unit="kg/s", desc="Mass flow")
        self.add_variable("p", unit="pa", desc="Pressure")
        self.add_variable("T", unit="K", desc="Temperature")
        self.add_variable("cp", 1004.0, unit="J/K/kg", desc="Heat capacity at constant pressure")
