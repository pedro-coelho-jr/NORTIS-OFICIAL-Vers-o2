# External imports
import geopandas as gpd
import pandas as pd

def get_dfs_from_selected_points(event):
    """
    Processa os pontos selecionados no mapa e retorna DataFrames separados para lotes, 
    estabelecimentos e pontos de mobilidade.
    
    Args:
        event: Objeto de evento do Streamlit contendo os pontos selecionados
        
    Returns:
        tuple: (sel_lote, sel_estab, sel_mob) - DataFrames contendo os dados selecionados
    """
    # Initialize empty DataFrames
    sel_lote = pd.DataFrame(columns=['SQL', 'Latitude', 'Longitude', 'Zoneamento', 'Area'])
    sel_mob = pd.DataFrame(columns=['Latitude', 'Longitude'])
    sel_estab = pd.DataFrame(columns=['Latitude', 'Longitude'])

    # Extract selected points
    if event and event.selection:
        for point in event.selection["points"]:
            customdata = point.get("customdata")
            if customdata:
                dataType = customdata[0]
                # In case the selection is a lote
                if dataType == "lote":
                    coordinates = point.get("ct")
                    new_row = pd.DataFrame({
                        'SQL': [customdata[3]],
                        'Latitude': [coordinates[1]],
                        'Longitude': [coordinates[0]], 
                        'Zoneamento': [customdata[2]],
                        'Area': [customdata[1]]
                    })
                    sel_lote = pd.concat([sel_lote, new_row], ignore_index=True)
                elif dataType == "estabelecimento":
                    new_row = pd.DataFrame({
                        'Latitude': [point.get("lat")],
                        'Longitude': [point.get("lon")]
                    })
                    sel_estab = pd.concat([sel_estab, new_row], ignore_index=True)
                elif dataType == "mobilidade":
                    new_row = pd.DataFrame({
                        'Latitude': [point.get("lat")],
                        'Longitude': [point.get("lon")]
                    })
                    sel_mob = pd.concat([sel_mob, new_row], ignore_index=True)

    return sel_lote, sel_estab, sel_mob

def filter_estabelecimentos_by_distance(estabelecimentos_df, selection_df, radius_km):
    """
    Filtra os estabelecimentos que estão dentro de radius_km de qualquer ponto em selection_df.
    
    Parameters:
    - estabelecimentos_df (pd.DataFrame): DataFrame com colunas 'Latitude' e 'Longitude'.
    - selection_df (pd.DataFrame): DataFrame com colunas 'Latitude' e 'Longitude' dos pontos selecionados.
    - radius_km (float): Raio de filtragem em quilômetros.
    
    Returns:
    - filtered_estabelecimentos (gpd.GeoDataFrame): GeoDataFrame filtrado.
    """
    
    # Converter estabelecimentos para GeoDataFrame
    estabelecimentos_gdf = gpd.GeoDataFrame(
        estabelecimentos_df,
        geometry=gpd.points_from_xy(estabelecimentos_df.Longitude, estabelecimentos_df.Latitude),
        crs="EPSG:4326"  # Coordenadas geográficas
    )

    # Converter pontos selecionados para GeoDataFrame
    selection_gdf = gpd.GeoDataFrame(
        selection_df,
        geometry=gpd.points_from_xy(selection_df.Longitude, selection_df.Latitude),
        crs="EPSG:4326"
    )

    # Projetar para um CRS métrico (Web Mercator)
    estabelecimentos_gdf = estabelecimentos_gdf.to_crs(epsg=3857)
    selection_gdf = selection_gdf.to_crs(epsg=3857)

    # Criar buffers ao redor dos pontos selecionados
    selection_gdf['buffer'] = selection_gdf.geometry.buffer(radius_km * 1000)  # Converter km para metros

    # Combinar todos os buffers em uma única geometria
    total_buffer = selection_gdf['buffer'].unary_union
    
    # Filtrar estabelecimentos dentro do buffer
    filtered_estabelecimentos = estabelecimentos_gdf[estabelecimentos_gdf.geometry.within(total_buffer)]

    # Calcular a distância de cada estabelecimento ao ponto selecionado mais próximo
    filtered_estabelecimentos['Distancia (m)'] = filtered_estabelecimentos.geometry.apply(
        lambda geom: selection_gdf.distance(geom).min()  # Converter metros para quilômetros
    )

    # round para 0 casas decimais e torne int
    filtered_estabelecimentos['Distancia (m)'] = filtered_estabelecimentos['Distancia (m)'].round(0).astype(int)

    # Converter de volta para o CRS original se necessário
    filtered_estabelecimentos = filtered_estabelecimentos.to_crs(epsg=4326)

    filtered_estabelecimentos_df = filtered_estabelecimentos.drop(columns='geometry')

    return filtered_estabelecimentos_df

def filter_mobility_points_by_distance(mobilidade, selection_df, radius_km):
    """
    Filtra os pontos de mobilidade que estão dentro de radius_km de qualquer ponto em selection_df.

    Parameters:
    - mobilidade (dict): Dicionário onde as chaves são os tipos de mobilidade e os valores são DataFrames com colunas 'Latitude' e 'Longitude'.
    - selection_df (pd.DataFrame): DataFrame com colunas 'Latitude' e 'Longitude' dos pontos selecionados.
    - radius_km (float): Raio de filtragem em quilômetros.

    Returns:
    - filtered_mobility (pd.DataFrame): DataFrame combinado com todos os pontos de mobilidade filtrados.
    """
    filtered_mobility_list = []

    for tipo, mobility_df in mobilidade.items():
        if mobility_df is not None and not mobility_df.empty:
            # Converter pontos de mobilidade para GeoDataFrame
            mobility_gdf = gpd.GeoDataFrame(
                mobility_df,
                geometry=gpd.points_from_xy(mobility_df.Longitude, mobility_df.Latitude),
                crs="EPSG:4326"  # Coordenadas geográficas
            )

            # Converter pontos selecionados para GeoDataFrame
            selection_gdf = gpd.GeoDataFrame(
                selection_df,
                geometry=gpd.points_from_xy(selection_df.Longitude, selection_df.Latitude),
                crs="EPSG:4326"
            )

            # Projetar para um CRS métrico (Web Mercator)
            mobility_gdf = mobility_gdf.to_crs(epsg=3857)
            selection_gdf = selection_gdf.to_crs(epsg=3857)

            # Criar buffers ao redor dos pontos selecionados
            selection_gdf['buffer'] = selection_gdf.geometry.buffer(radius_km * 1000)  # Converter km para metros

            # Combinar todos os buffers em uma única geometria
            total_buffer = selection_gdf['buffer'].unary_union

            # Filtrar pontos dentro do buffer
            filtered_gdf = mobility_gdf[mobility_gdf.geometry.within(total_buffer)].copy()

            # Calcular a distância de cada ponto ao ponto selecionado mais próximo
            filtered_gdf['Distancia (m)'] = filtered_gdf.geometry.apply(
                lambda geom: selection_gdf.distance(geom).min()
            ).round(0).astype(int)

            # Adicionar o tipo de mobilidade ao DataFrame filtrado
            filtered_gdf['Tipo'] = tipo

            # Converter de volta para CRS original e armazenar
            filtered_gdf = filtered_gdf.to_crs(epsg=4326)
            filtered_mobility_list.append(filtered_gdf)

    if filtered_mobility_list:
        return pd.concat(filtered_mobility_list).drop(columns='geometry')
    else:
        return pd.DataFrame()
