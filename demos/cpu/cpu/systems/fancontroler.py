from cosapp.systems import System


class FanControler(System):
    """ 
    Define tension for fan from the level of CPU temperature
    """
    def setup(self):
        # inputs
        self.add_inward("T_cpu", unit="degC", desc="CPU temperature")
        self.add_inward("low_threshold", 40., unit="degC", desc="Low to medium temperature threshold")
        self.add_inward("high_threshold", 60., unit="degC", desc="Medium to high temperature threshold")
        self.add_inward("low_tension", 0.0, unit="V", desc="Output low tension")
        self.add_inward("medium_tension", 6.0, unit="V", desc="Output medium tension")
        self.add_inward("max_tension", 12.0, unit="V", desc="Output max tension")
        self.add_inward("tension_command", 12.0, unit="V", desc="Output command tension")

        # outputs
        self.add_outward("tension", 0.0, unit="V", desc="Output tension")

        self.add_event('null_to_low_tension', trigger="T >= low_threshold")
        self.add_event('low_to_max_tension', trigger="T >= high_threshold")
        self.add_event('low_to_null_tension', trigger="T <= low_threshold")
        self.add_event('max_to_low_tension', trigger="T <= high_threshold")

    def compute(self):
        self.tension = self.tension_command

    def transition(self):
        if self.low_to_null_tension.present:
            self.tension_command = 0.
        elif self.null_to_low_tension.present or self.max_to_low_tension.present:
            self.tension_command = self.medium_tension
        else:
            self.tension_command = self.max_tension
