# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache-2.0

import ipywidgets as widgets
from pyoccad.render import JupyterThreeJSRenderer, JupyterThreeJSRenderer2d


def render_view(shape, size=(600, 600), position=(-1.0, 0, 0), view_2D=False):
    view_obj = JupyterThreeJSRenderer2d if view_2D else JupyterThreeJSRenderer
    render = view_obj(view_size=size, camera_target=(1.0, 0.0, 0.0), camera_position=position)
    render_row = render.add_shape(
        shape, uid="blade", face_color="#156289", opacity=1.0, plot_edges=False
    )
    return render, render_row


def compare_with_image(s):
    """Compare with image."""
    file = open("../images/fan.png", "rb")
    image = file.read()
    img = widgets.Image(value=image, format="png", width=600, height=600)

    render, _ = render_view(s.geometry.shape)
    render2d, _ = render_view(s.geometry.shape, view_2D=True)

    blade_slider = widgets.IntSlider(
        value=7,
        min=5,
        max=9,
        step=1,
        description="Blade count:",
        disabled=False,
        continuous_update=True,
        orientation="horizontal",
        readout=True,
    )

    inlet_angle_slider = widgets.IntSlider(
        value=60,
        min=40,
        max=80,
        step=2,
        description="Inlet angle (deg):",
        disabled=False,
        continuous_update=True,
        orientation="horizontal",
        readout=True,
    )

    def on_count_value_change(change):
        s.rotor.count = change["new"]
        s.run_drivers()
        render.update_shape(s.geometry.shape, uid="blade")
        render2d.update_shape(s.geometry.shape, uid="blade")

    def on_inlet_angle_value_change(change):
        s.rotor.blade.inlet_angle = change["new"]
        s.run_drivers()
        render.update_shape(s.geometry.shape, uid="blade")
        render2d.update_shape(s.geometry.shape, uid="blade")

    blade_slider.observe(on_count_value_change, names="value")
    inlet_angle_slider.observe(on_inlet_angle_value_change, names="value")

    return widgets.HBox(
        [render2d.show(), img, render.show(), widgets.VBox([blade_slider, inlet_angle_slider])]
    )


def grid_display(s, render):
    """Display grid."""
    blade_slider = widgets.IntSlider(
        value=60,
        min=50,
        max=70,
        step=1,
        description="Blade count:",
        disabled=False,
        continuous_update=True,
        orientation="horizontal",
        readout=True,
    )

    inlet_angle_slider = widgets.IntSlider(
        value=60,
        min=40,
        max=80,
        step=2,
        description="Inlet angle (deg):",
        disabled=False,
        continuous_update=True,
        orientation="horizontal",
        readout=True,
    )

    def on_count_value_change(change):
        s.count = change["new"]
        s.run_drivers()
        render.update_shape(s.geometry, uid="row")

    def on_inlet_angle_value_change(change):
        s.blade.inlet_angle = change["new"]
        s.run_drivers()
        render.update_shape(s.geometry, uid="row")

    blade_slider.observe(on_count_value_change, names="value")
    inlet_angle_slider.observe(on_inlet_angle_value_change, names="value")

    return widgets.HBox([render.show(), widgets.VBox([blade_slider, inlet_angle_slider])])
