from typing import Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots


def plot_recorders(
    recs: dict[str, pd.DataFrame],
    pplots: Sequence[Sequence[tuple[str, str]]],
    title_text: str = "CPU simulation analysis",
    **layout_kwargs,
) -> None:
    """Display grouped figures with proper x/y axis labels."""

    rows = len(pplots)
    cols = max(len(row) for row in pplots)

    fig = make_subplots(rows=rows, cols=cols, horizontal_spacing=0.1, vertical_spacing=0.1)
    for i in range(1, rows * cols + 1):
        fig.update_xaxes(
            showgrid=True, gridcolor="#EBF0F8", row=(i - 1) // cols + 1, col=(i - 1) % cols + 1
        )
        fig.update_yaxes(
            showgrid=True, gridcolor="#EBF0F8", row=(i - 1) // cols + 1, col=(i - 1) % cols + 1
        )

    # Define a list of colors to use for the different recorder types
    colors = px.colors.qualitative.Plotly

    for i, row in enumerate(pplots, start=1):
        for j, (x, y) in enumerate(row, start=1):
            for k, (rec_name, df) in enumerate(recs.items()):
                if x in df.columns and y in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df[x],
                            y=df[y],
                            mode="lines+markers",
                            name=rec_name,
                            line=dict(color=colors[k]),
                            showlegend=(i == 1 and j == 1),
                        ),
                        row=i,
                        col=j,
                    )

            # Set individual axis labels
            fig.update_xaxes(title_text=x, row=i, col=j)
            fig.update_yaxes(title_text=y, row=i, col=j)

    fig.update_layout(
        height=layout_kwargs.get("height", 300 * rows),
        width=layout_kwargs.get("width", 400 * cols),
        title={
            "text": title_text,
            "x": 0.5,  # centers the title
            "xanchor": "center",
            "font": {"size": 24},  # increase font size here
        },
        hovermode="x unified",
        plot_bgcolor="white",
    )
    fig.update_layout(**layout_kwargs)

    fig.show()
