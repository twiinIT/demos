# Copyright (C) 2024, twiinIT
# SPDX-License-Identifier: Apache-2.0

import ipywidgets
import plotly.graph_objs as go


def plot_recorders(recs, pplots, title="", **kwargs):
    """plot_recorders."""
    plots = []
    vsize = len(pplots)
    hsize = len(pplots[0])
    width = 300 * hsize
    height = 400 * vsize
    for r in pplots:
        r_plots = []
        for p in r:
            x, y = p
            x, xlabel = x.popitem() if isinstance(x, dict) else (x, x)
            y, ylabel = y.popitem() if isinstance(y, dict) else (y, y)

            plot_options = dict(
                width=width,
                height=height,
                xaxis={
                    "title": {"text": f"{xlabel}", "font": {"size": 20}},
                    "gridcolor": "#EBF0F8",
                },
                yaxis={
                    "title": {"text": f"{ylabel}", "font": {"size": 20}},
                    "gridcolor": "#EBF0F8",
                },
                # legend={
                #     "x": 0.35,
                #     "y": 0.25,
                #     "font": {"size": 20},
                #     "orientation": "h",
                #     "xanchor": "center",
                # },
                plot_bgcolor="white",
                hovermode="x",
            )
            plot_options.update(kwargs)

            r_plots.append(
                go.FigureWidget(
                    data=[
                        go.Scatter(
                            x=r[x],
                            y=r[y],
                            mode="markers",
                            name=n,
                        )
                        for n, r in recs.items()
                        if x in r and y in r
                    ],
                    layout=go.Layout(**plot_options),
                )
            )
        plots.append(ipywidgets.HBox(r_plots))

    return ipywidgets.VBox(plots)
