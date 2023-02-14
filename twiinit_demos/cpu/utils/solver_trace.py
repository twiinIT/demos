import plotly.graph_objs as go
import numpy as np
import pandas as pd


def plot_solver_trace(solver, *args, **kwargs):

    trace = list(solver._NonLinearSolver__trace)
    unknowns = list(solver.problem.unknowns.keys())
    residues = list(solver.problem.residues.keys())

    for step in trace:
        step.update({unknowns[i]: val for i, val in enumerate(step["x"])})
        step.update({residues[i]: val for i, val in enumerate(step["residues"])})

    df = pd.DataFrame(trace)
    names = list(args)
    if len(names) == 0:
        names = unknowns + residues

    plot_options = dict(
        width=1800,
        height=800,
        xaxis={"title": {"text": "index (-)", "font": {"size": 12}}, "gridcolor": "#EBF0F8"},
        yaxis={"gridcolor": "#EBF0F8"},
        plot_bgcolor="white",
        hovermode="x",
    )
    plot_options.update(kwargs)

    return go.Figure(
        data=[
            go.Scatter(
                x=df.index,
                y=df[n],
                mode="markers",
                name=n,
            )
            for n in names
        ],
        layout=go.Layout(**plot_options),
    )
