import plotly.graph_objects as go
import numpy as np

def plot_mobility_scattermapbox(fig, mobility_selected, mobilidade, LINE_MOBILITIES, LINE_COLORS, COLOR_DICT_MOBILITY):
    """
    Adiciona camadas de mobilidade ao mapa Plotly
    
    Args:
        fig: Figura Plotly base
        mobility_selected: Lista de tipos de mobilidade selecionados
        mobilidade: Dicionário com dados de mobilidade
        LINE_MOBILITIES: Lista de tipos de mobilidade que são linhas
        LINE_COLORS: Dicionário de cores para linhas de metrô
        COLOR_DICT_MOBILITY: Dicionário de cores para tipos de mobilidade
    
    Returns:
        fig: Figura Plotly atualizada com as camadas de mobilidade
    """

    if mobility_selected:
        for tipo in mobility_selected:
            df_mobility = mobilidade.get(tipo)
            if df_mobility is not None and not df_mobility.empty:
                if tipo in LINE_MOBILITIES:
                    if tipo in ['Linha metro projeto', 'Linha metro'] and 'lmt_nome' in df_mobility.columns:
                        for nome_linha, grupo in df_mobility.groupby('lmt_nome'):
                            cor_linha = LINE_COLORS.get(nome_linha.upper(), 'blue')
                            line_style = dict(color=cor_linha, width=3)
                            if tipo == 'Linha metro projeto':
                                line_style['dash'] = 'dot'

                            full_lats, full_lons = [], []
                            for geom in grupo.geometry:
                                if geom.geom_type == 'LineString':
                                    coords = list(geom.coords)
                                    lats = [c[1] for c in coords]
                                    lons = [c[0] for c in coords]
                                    if full_lats:
                                        full_lats.append(None)
                                        full_lons.append(None)
                                    full_lats.extend(lats)
                                    full_lons.extend(lons)

                            fig.add_trace(go.Scattermapbox(
                                lat=full_lats,
                                lon=full_lons,
                                mode='lines',
                                line=line_style,
                                name=f"{tipo} - {nome_linha}",
                                text=f"{tipo}: {nome_linha}",
                                hoverinfo='text',
                                opacity=0.3
                            ))
                    else:
                        default_color = COLOR_DICT_MOBILITY.get(tipo, 'blue')
                        full_lats, full_lons = [], []
                        for geom in df_mobility.geometry:
                            if geom.geom_type == 'LineString':
                                coords = list(geom.coords)
                                lats = [c[1] for c in coords]
                                lons = [c[0] for c in coords]
                                if full_lats:
                                    full_lats.append(None)
                                    full_lons.append(None)
                                full_lats.extend(lats)
                                full_lons.extend(lons)

                        fig.add_trace(go.Scattermapbox(
                            lat=full_lats,
                            lon=full_lons,
                            mode='lines',
                            line=dict(color=default_color, width=3),
                            name=tipo,
                            text=tipo,
                            hoverinfo='text',
                            opacity=0.3
                        ))
                else:
                    point_size = 8	
                    if tipo == 'Estacao de Metro':
                        point_size = 32
                    elif tipo == 'Estacao de Trem':
                        point_size = 32

                    elif tipo == 'Ponto de onibus':
                        point_size = 5
                    
                    fig.add_trace(go.Scattermapbox(
                        lat=df_mobility['Latitude'],
                        lon=df_mobility['Longitude'],
                        mode='markers',
                        marker=dict(size=point_size, color=COLOR_DICT_MOBILITY.get(tipo, 'blue'), opacity=0.8),
                        name=tipo,
                        cluster={"enabled": False},
                        text=tipo,
                        hoverinfo='text',
                        customdata=np.column_stack((
                            np.repeat("mobilidade", len(df_mobility)),
                            np.repeat(tipo, len(df_mobility))
                        )),
                        selected=dict(marker=dict(opacity=0.9)),
                        unselected=dict(marker=dict(opacity=0.9)),
                    ))
    
    return fig