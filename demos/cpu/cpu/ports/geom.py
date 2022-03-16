from cosapp.ports import Port


class GeomPort(Port):
    def setup(self):
        self.add_variable("visible", True)
        self.add_variable("shape", None)
