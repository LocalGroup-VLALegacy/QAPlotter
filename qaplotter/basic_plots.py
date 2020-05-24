
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def basic_scatter(tab, xvar='x', yvar='y', hover='ants',
                  colorvar='ant1', meta=None):

    if hover == 'ants':
        # Note that the slicing here is OPPOSITE the numpy convention.
        # Hence the transpose on custom_data.
        hovertemplate = 'Ant1: %{customdata[0]} <br>Ant2 %{customdata[1]}'

        custom_data = np.vstack((tab['ant1'].tolist(),
                                 tab['ant2'].tolist())).T
    else:
        raise NotImplementedError("")

    fig = go.Figure(data=go.Scattergl(x=tab[xvar],
                                      y=tab[yvar],
                                      mode='markers',
                                      marker=dict(size=16,
                                                  cmax=tab[colorvar].max(),
                                                  cmin=tab[colorvar].min(),
                                                  color=tab[colorvar].tolist(),
                                                  colorscale=px.colors.qualitative.Safe),
                                      customdata=custom_data,
                                      hovertemplate=hovertemplate))
    if meta is not None:
        fig.update_layout(
            title=f"Field: {meta['field']}<br>SPW: {meta['spw']}<br>Scan: {meta['scan']}<br>MS: {meta['vis']}",
            # NEED TO PASS x, y names!!
            xaxis_title="uv-distance (m)",
            yaxis_title="Amplitude",
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#7f7f7f")
        )

    fig.show()
