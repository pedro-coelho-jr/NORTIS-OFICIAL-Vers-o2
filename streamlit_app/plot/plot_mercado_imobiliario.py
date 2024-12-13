import plotly.express as px
import plotly.colors as mcolors

# Constants
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoicHJvamV0b2RhZG9zIiwiYSI6ImNtMXdiOTEydDA1czEyaW41MDYwamIwdGQifQ.CntGc8JTYWf6b9tveFDAVQ"

# Set the Mapbox access token globally
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

# Functions
def plot_mercado_imobiliario(df, width=400, height=1200, center=(-23.55028, -46.63389), mapbox_style="carto-positron", color_var=None, hover_data=None, dot_size=10, dot_color='blue'):
    """
    Plot points on a map using latitude and longitude coordinates
    
    Args:
        df: DataFrame containing Latitude and Longitude columns
        width: Width of the plot in pixels
        height: Height of the plot in pixels
        center: Center coordinates of the map
        mapbox_style: Style of the mapbox map
        color_var: Column name to use for coloring points
        hover_data: List of columns to show in hover tooltip
        dot_size: Size of the dots on the map
        dot_color: Color of the dots if color_var is not specified
    """
    # Handle custom Mapbox styles
    if mapbox_style == "satellite-streets":
        mapbox_style = "mapbox://styles/mapbox/satellite-streets-v12"
    if mapbox_style == "satellite":
        mapbox_style = "mapbox://styles/mapbox/satellite-v9"


    # Personalizar o texto de hover
    hover_template = (
        "<b>Empreendimento:</b> %{customdata[0]}<br>" +
        "<b>Grupo:</b> %{customdata[1]}<br>" +
        "<b>Torres:</b> %{customdata[3]}<br>" +
        "<b>Soma Estoque:</b> %{customdata[4]}<extra></extra>"
    )

    # Plot the data
    fig = px.scatter_mapbox(df,
                           lat='Latitude',
                           lon='Longitude',
                           color=color_var,
                           mapbox_style=mapbox_style,
                           zoom=13,
                           center={"lat": center[0], "lon": center[1]},
                           hover_data=hover_data,
                           width=width,
                           height=height,
                           color_discrete_sequence=dot_color,
                           labels={"color": "empreendimento"}
                           )
    # Update marker size and hover template
    fig.update_traces(marker=dict(size=dot_size), hovertemplate=hover_template)

    # Update layout
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Posicionar a legenda sobre o gráfico
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(30, 30, 50, 0.8)"  # fundo branco semi-transparente
        )
    )

    return fig
