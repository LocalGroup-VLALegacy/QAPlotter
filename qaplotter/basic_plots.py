
import plotly.graph_objects as go


def basic_scatter(tab, xvar='x', yvar='y'):

    fig = go.Figure(data=go.Scattergl(x=tab[xvar],
                                      y=tab[yvar],
                                      mode='markers',
                                      marker=dict(color='black')))
    fig.show()
