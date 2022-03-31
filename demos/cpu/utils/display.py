import ipywidgets as widgets


def compare_with_image(s, render):
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
        continuous_update=False,
        orientation='horizontal',
        readout=True
    )

    def on_value_change(change):
        s.rotor.count = change['new']
        s.run_drivers()
        render.update_shape(s.geometry.shape, uid="blade");

    blade_slider.observe(on_value_change, names='value')

    return widgets.HBox([img, render.show(), widgets.VBox([blade_slider, ])])