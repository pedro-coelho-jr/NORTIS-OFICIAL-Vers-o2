import plotly.graph_objects as go
import plotly.colors as mcolors

# Constants
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoicHJvamV0b2RhZG9zIiwiYSI6ImNtMXdiOTEydDA1czEyaW41MDYwamIwdGQifQ.CntGc8JTYWf6b9tveFDAVQ"

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
    if mapbox_style == "open-street-map":
        mapbox_style = "mapbox://styles/mapbox/streets-v12"
    


    # Personalizar o texto de hover
    hover_template = (
        "<b>Empreendimento:</b> %{customdata[0]}<br>" +
        "<b>Grupo:</b> %{customdata[1]}<br>" +
        "<b>Torres:</b> %{customdata[3]}<br>" +
        "<b>Soma Estoque:</b> %{customdata[4]}<extra></extra>"
    )

    # Criar figura usando go em vez de px
    fig = go.Figure()

    # Criar mapeamento de cores se color_var for especificado
    if color_var:
        # Obter valores únicos da coluna
        unique_values = sorted(df[color_var].unique())
        # Criar um dicionário mapeando cada valor para uma cor
        color_map = dict(zip(unique_values, mcolors.qualitative.Set2))
        
        # Criar um trace separado para cada valor único
        for value in unique_values:
            mask = df[color_var] == value
            fig.add_trace(go.Scattermap(
                lat=df.loc[mask, 'Latitude'],
                lon=df.loc[mask, 'Longitude'],
                mode='markers',
                marker=dict(
                    size=dot_size,
                    color=color_map[value]
                ),
                name=str(value),  # Adiciona o nome para a legenda
                customdata=df[mask][hover_data].values if hover_data else None,
                hovertemplate=hover_template
            ))
    else:
        # Caso não tenha color_var, adiciona um único trace
        fig.add_trace(go.Scattermap(
            lat=df['Latitude'],
            lon=df['Longitude'],
            mode='markers',
            marker=dict(
                size=dot_size,
                color=dot_color
            ),
            customdata=df[hover_data].values if hover_data else None,
            hovertemplate=hover_template
        ))

    # Configurar o layout
    fig.update_layout(
        mapbox=dict(
            accesstoken=MAPBOX_ACCESS_TOKEN,
            style=mapbox_style,
            center=dict(lat=center[0], lon=center[1]),
            zoom=13
        ),
        width=width,
        height=height,
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(30, 30, 50, 0.8)"
        )
    )

    return fig
