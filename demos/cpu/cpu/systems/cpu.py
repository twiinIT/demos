from cosapp.systems import System


class CPU(System):
    def setup(self):
        self.add_inward("usage", 20.0, desc="Usage percentage")
        self.add_inward("tdp", 105.0, "W", desc="Thermal Design Power")
        self.add_inward("heat_flow", 0.0, desc="Exit thermal flow")
        self.add_inward("heat_capacity", 5.0, "J/K", desc="CPU heat capacity")
        self.add_inward("T", 273.15, unit="K", desc="Metal temperature")

        self.add_outward("power", 20.0, unit="W", desc="Power")

        self.add_transient("T", der="(power - heat_flow) / heat_capacity", desc="Enthalpy delta")

    def compute(self):
        self.power = self.tdp * self.usage / 100.0
