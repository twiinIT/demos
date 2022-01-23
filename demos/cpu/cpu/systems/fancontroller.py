from cosapp.systems import System


class FanController(System):
    """ 
    Define tension for fan from the level of CPU temperature
    """
    def setup(self):
        # inputs
        self.add_inward("T", unit="K", desc="Temperature")
        self.add_inward("low_threshold", 303.15, desc="Low to medium temperature threshold")
        self.add_inward("high_threshold", 333.15, desc="Medium to high temperature threshold")
        self.add_inward("low_tension", 0.0, desc="Output low tension")
        self.add_inward("medium_tension", 6.0, desc="Output medium tension")
        self.add_inward("max_tension", 12.0, desc="Output max tension")

        # outputs
        self.add_outward("tension", 0.0, desc="Output tension")

    def compute(self):
        if self.T <= self.low_threshold:
            self.tension = self.low_tension
        elif self.T <= self.high_threshold:
            self.tension = self.medium_tension
        else:
            self.tension = self.max_tension
