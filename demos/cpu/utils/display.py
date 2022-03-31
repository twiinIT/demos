import ipywidgets as widgets


def compare_with_image(s, render2d, render):
    file = open("images/fan.png", "rb")
    image = file.read()
    img = widgets.Image(
        value=image,
        format='png',
        width=600,
        height=600,
    )

    blade_slider = widgets.IntSlider(
        value=7,
        min=5,
        max=9,
        step=1,
        description='Blade count:',
        disabled=False,
        continuous_update=True,
        orientation='horizontal',
        readout=True
    )

    inlet_angle_slider = widgets.IntSlider(
        value=60,
        min=40,
        max=80,
        step=2,
        description='Inlet angle (deg):',
        disabled=False,
        continuous_update=True,
        orientation='horizontal',
        readout=True
    )
        
    def on_count_value_change(change):
        s.rotor.count = change['new']
        s.run_drivers()
        render.update_shape(s.geometry.shape, uid="blade");
        render2d.update_shape(s.geometry.shape, uid="blade");

    def on_inlet_angle_value_change(change):
        s.rotor.blade.inlet_angle = change['new']
        s.run_drivers()
        render.update_shape(s.geometry.shape, uid="blade");
        render2d.update_shape(s.geometry.shape, uid="blade");

    blade_slider.observe(on_count_value_change, names='value')
    inlet_angle_slider.observe(on_inlet_angle_value_change, names='value')

    return widgets.HBox([render2d.show(), img, render.show(), widgets.VBox([blade_slider, inlet_angle_slider])])