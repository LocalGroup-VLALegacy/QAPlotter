
import plotly.graph_objects as go
import numpy as np


def basic_scatter(tab, xvar='x', yvar='y', hover='ants'):

    if hover == 'ants':
        hovertemplate = 'Ant1: %{customdata[0]} <br>Ant2 %{customdata[1]}'

        custom_data = np.vstack((tab['ant1'].tolist(),
                                 tab['ant2'].tolist())).T

    fig = go.Figure(data=go.Scattergl(x=tab[xvar],
                                      y=tab[yvar],
                                      mode='markers',
                                      marker=dict(color='black'),
                                      customdata=custom_data,
                                      hovertemplate=hovertemplate))
    fig.show()
