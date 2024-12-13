import streamlit as st
import geopandas as gpd
import pandas as pd
import os
import plotly.graph_objects as go
import numpy as np
from unidecode import unidecode

# internal imports
from plot.plot_zones import plot_zones_with_colors
from plot.Distritos import plot_borders
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio
from pages.utils.principal import get_dfs_from_selected_points, filter_estabelecimentos_by_distance, filter_mobility_points_by_distance
from pages.utils.utils import load_geojson, convert_to_int, load_all_xlsx_in_directory, categorizar_estabelecimento, load_mobility_data
from pages.utils.constants import (
    DISTRITOS_CENTRO, DISTRITOS_LESTE, DISTRITOS_NORTE, DISTRITOS_OESTE, DISTRITOS_SUL,
    COLOR_MAP, COLOR_DICT_ESTABELECIMENTOS, COLOR_DICT_MOBILITY, LINE_COLORS, LINE_MOBILITIES
)
from pages.utils.pontuacao import gerar_pontuacao
from pages.utils.pontuacao import exibir_score

### PAGE CONFIG ###
st.set_page_config(layout="wide")

@st.cache_data
def cache(dataframe):
    return dataframe
### FUNCTIONS SECTION ###   
@st.cache_data
def load_zone_geojson_or_shp(directory_path):
    # Lista para armazenar os GeoDataFrames
    gdf_list = []

    # Iterar sobre os arquivos no diretório
    for filename in os.listdir(directory_path):
        if filename.endswith('.geojson') or filename.endswith('.shp'): # Verifique as extensões necessárias
            file_path = os.path.join(directory_path, filename)
            gdf = gpd.read_file(file_path)  # Carregar o GeoDataFrame
            gdf_list.append(gdf)  # Adicionar o GeoDataFrame à lista

    # Concatenar todos os GeoDataFrames em um único
    combined_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
    return combined_gdf

### STARTING DATA SECTION ###
distritos = encontrar_arquivo('distritos.geojson')
sp_distritos = load_geojson(distritos)

#Ler dados de mobilidade
# Configuração dos diretórios
xlsx_directory = encontrar_diretorio('mobilidade_ponto')
geojson_directory = encontrar_diretorio('mobilidade_linha_linestring')
geojson_files = [
    'Ferrovia mdc.geojson',
    'Linha metro.geojson',
    'Linha metro projeto.geojson',
    'Linha trem.geojson',
    'Linha trem projeto.geojson',
]

# Carregar dados de mobilidade
mobilidade = load_mobility_data(xlsx_directory, geojson_directory, geojson_files)
# Dados de mobilidade plotaveis nos graficos
mobilidade_analisavel = load_all_xlsx_in_directory(xlsx_directory)
mobilidade_analisavel = cache(mobilidade_analisavel)

# Lookup zonas fora de operacao urbana NORTIS
operacao_urbana_n = encontrar_arquivo('Zonas_fora_de_operacao_urbana_att_2.xlsx')
lookup_f_op_n = pd.read_excel(operacao_urbana_n)
lookup_f_op_n["Potencial para projeto imobiliário?"] = lookup_f_op_n["Potencial para projeto imobiliário"].map(
    {1: True, 0: False})
potenciais_possiveis = lookup_f_op_n['Potencial'].unique()
territorio_possiveis = lookup_f_op_n['Território'].unique()
# lookup zonas fora de operacao urbana Vibra
operacao_urbana_v = encontrar_arquivo('Zonas_operacao_urbana_completo_Vibra.xlsx')
lookup_f_op_v = pd.read_excel(operacao_urbana_v)
lookup_f_op_v["Potencial para projeto imobiliário?"] = lookup_f_op_n["Potencial para projeto imobiliário"].map(
    {1: True, 0: False})
potenciais_possiveis_v = lookup_f_op_v['Potencial'].unique()
territorio_possiveis_v = lookup_f_op_v['Território'].unique()
# Empresas
empresas_possiveis = ['NORTIS','VIBRA']
# Carregar dados de renda média (desnecessário)
arquivo_renda = encontrar_arquivo('Renda_Por_Faixa_Distritos.xlsx')
df_renda = pd.read_excel(arquivo_renda, sheet_name='Renda Média', skiprows=1)
    # Remover acentos e converter para maiúsculas nos nomes dos distritos
df_renda['Distritos'] = df_renda['Distritos'].apply(lambda x: unidecode(str(x)).upper())
    # Converter a coluna 'Renda Média' para o formato float
df_renda['Renda Média'] = df_renda['Renda Média'].apply(lambda x: float(str(x).replace(',', '')))
# Carregar dados de domicílios por faixa de renda
arquivo_domicilios = encontrar_arquivo('Renda_Por_Faixa_Distritos.xlsx')
df_domicilios = pd.read_excel(arquivo_domicilios, sheet_name='Resultados', skiprows=0)
df_domicilios.iloc[:, 1:] = df_domicilios.iloc[:, 1:].map(convert_to_int)
    # Remover acentos e converter para maiúsculas nos nomes dos distritos
df_domicilios['Distritos'] = df_domicilios['Distritos'].apply(lambda x: unidecode(str(x)).upper())


shapefile_favela = encontrar_arquivo('favelas_final.geojson')
gdf_favela = gpd.read_file(shapefile_favela)

shapefile_inundavel = encontrar_arquivo('inundavel.geojson')
gdf_inundavel = gpd.read_file(shapefile_inundavel)

arquivo_populacao = encontrar_arquivo('populacao_por_distrito_2010.xlsx')
df_populacao = pd.read_excel(arquivo_populacao)
df_populacao['População'] = df_populacao['População'].astype(int)
df_populacao['Distrito'] = df_populacao['Distrito'].apply(lambda x: unidecode(str(x)).upper())

arquivo_densidade = encontrar_arquivo('densidade_demografica_por_distrito_2022.xlsx')
df_densidade = pd.read_excel(arquivo_densidade)
df_densidade['Distrito'] = df_densidade['Distrito'].apply(lambda x: unidecode(str(x)).upper())

# Initialize map_selection_df
st.session_state.map_selection_df = pd.DataFrame()
st.session_state.event = None


### SIDEBAR SECTION ###
with st.sidebar:

    # FILTROS
    filtro_empresas = st.selectbox('Empresa',empresas_possiveis,index = 0)
    filtro_potencial = st.multiselect('Potencial', potenciais_possiveis, default=potenciais_possiveis)
    if filtro_empresas == 'NORTIS':
        lookup_filtered = lookup_f_op_n[(lookup_f_op_n['Potencial'].isin(filtro_potencial))]
    elif filtro_empresas == 'VIBRA':
        lookup_filtered = lookup_f_op_v[(lookup_f_op_v['Potencial'].isin(filtro_potencial))]
    zonas_selecionadas = st.multiselect('Zonas de Interesse', sorted(lookup_filtered['Tipo de Zona'].unique()))
    distritos_filtrados = []
    # Se não houver zonas selecionadas, não fazer nada
    if zonas_selecionadas:
        gdf_filtered_list = []
        # Iterar sobre cada zona filtrada
        # Esse for loop aqui é para carregar os arquivos das zonas de interesse
        # Será removido com o datalake
        for zona in zonas_selecionadas:
            # Encontrar o diretório para cada zona
            arquivo_zona_filtrada = encontrar_diretorio(zona)
            # Carregar os dados correspondentes
            gdf = load_zone_geojson_or_shp(arquivo_zona_filtrada)
            # Adicionar ao lista de dados filtrados
            gdf_filtered_list.append(gdf)
    
        # geodataframe com todos os lotes filtrados
        gdf_filtered = pd.concat(gdf_filtered_list, ignore_index=True)
        tipo_filtrado = st.multiselect('tipo', sorted(gdf_filtered['tipo'].unique()), default=gdf_filtered['tipo'].unique())
        gdf_filtered = gdf_filtered[gdf_filtered['tipo'].isin(tipo_filtrado)]
        exibir_vendas = st.toggle('Exibir vendas ITBI')
        distritos_possiveis = gdf_filtered['NOME_DIST'].unique()
        regioes_map = {'CENTRO': DISTRITOS_CENTRO, 'NORTE': DISTRITOS_NORTE, 'SUL': DISTRITOS_SUL, 'LESTE': DISTRITOS_LESTE, 'OESTE': DISTRITOS_OESTE}
        regioes_possiveis = []
        for regiao, distritos in regioes_map.items():
            if any(distrito in distritos_possiveis for distrito in distritos):
                regioes_possiveis.append(regiao)
        regiao_filtrada = st.multiselect('Regiões de Interesse', regioes_possiveis)
        distritos_em_regioes = []
        for regiao in regiao_filtrada:
            distritos_em_regioes.extend(regioes_map[regiao])
        distritos_possiveis = list(set(distritos_em_regioes).intersection(distritos_possiveis))
        
        if regiao_filtrada and len(distritos_possiveis) >= 2:
            df_renda = df_renda[df_renda['Distritos'].isin(distritos_possiveis)]
            renda = st.slider('Faixa de renda', 
                              min_value=min(df_renda['Renda Média'].to_list()), 
                              max_value=max(df_renda['Renda Média'].to_list()), 
                              value=(min(df_renda['Renda Média']), max(df_renda['Renda Média'])))
        
            df_renda = df_renda[df_renda['Renda Média'].between(renda[0],renda[1])]
            distritos_renda = df_renda['Distritos'].to_list()
            distritos_possiveis = list(set(distritos_renda).intersection(distritos_possiveis))

            if len(distritos_possiveis) >=2 :
                df_populacao = df_populacao[df_populacao['Distrito'].isin(distritos_possiveis)]
                populacao = st.slider('População',
                                        min_value=min(df_populacao['População'].to_list()),
                                        max_value=max(df_populacao['População'].to_list()),
                                        value=(min(df_populacao['População']), max(df_populacao['População'])))
                df_populacao = df_populacao[df_populacao['População'].between(populacao[0],populacao[1])]
                distritos_populacao = df_populacao['Distrito'].to_list()
                distritos_possiveis = list(set(distritos_populacao).intersection(distritos_possiveis))

                if len(distritos_possiveis) >= 2:
                    df_densidade = df_densidade[df_densidade['Distrito'].isin(distritos_possiveis)]
                    densidade = st.slider('Densidade Demográfica',
                                          min_value=min(df_densidade['Densidade Demográfica'].to_list()),
                                          max_value=max(df_densidade['Densidade Demográfica'].to_list()),
                                          value=(min(df_densidade['Densidade Demográfica']), max(df_densidade['Densidade Demográfica'])))
                    df_densidade = df_densidade[df_densidade['Densidade Demográfica'].between(densidade[0],densidade[1])]
                    distritos_densidade = df_densidade['Distrito'].to_list()
                    distritos_possiveis = list(set(distritos_densidade).intersection(distritos_possiveis))

        # Selectbox para escolhermos distritos
        distritos_filtrados = st.selectbox('Distritos de Interesse', distritos_possiveis)

        # Escolha do tipo de mapa
        mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter', 'satellite-streets', 'satellite'])


        ## MOBILIDADE E ESTABELECIMENTOS SECTION ##
        # Initialize map_selection_df
        map_selection_df = pd.DataFrame()
        mobility_selected = []
        filtered_mobility_points = None
        mobility_types = list(mobilidade.keys())

        # Toggle para selecionar/deselecionar todos os pontos de mobilidade
        toggle_mobility = st.toggle("Mostrar Mobilidade", value=False)
        # Multiselect para os tipos de mobilidade
        if toggle_mobility:
            default_mobility_types = [tipo for tipo in mobility_types if
                                      tipo not in ["Linha metro projeto",
                                                   "Linha trem projeto",
                                                   "Projetos de Estacao de Metro",
                                                   "Projetos de Estacao de Trem"]]
            mobility_selected = st.multiselect(
                'Mobilidade',
                mobility_types,
                default=default_mobility_types  # Exclui as camadas "projeto" inicialmente
            )
            # Filtro de distância
            #distance = st.slider('Distância de pontos de mobilidade para analisar (m)', 100, 1000, 500, 100)
            #distance = distance/1000
            
        # mostrar estabelecimentos
        estabelecimentos = None
        toggle_comercio_servicos = st.toggle('Comércio e Serviços', value=False)
        toggle_educacao_e_saude = st.toggle('Educação e Saúde', value=False)
        toggle_feiras_livres = st.toggle('Feiras Livres', value=False)
        mostrar_favelas = st.toggle('Mostrar Comunidades', value=False)
        mostrar_inundavel = st.toggle('Mostrar Áreas Inundáveis', value=False)

        if toggle_comercio_servicos or toggle_educacao_e_saude or toggle_feiras_livres:
            estabelecimentos_path = encontrar_arquivo('estabelecimentos_dentro_contorno.csv')
            estabelecimentos = pd.read_csv(estabelecimentos_path)
            estabelecimentos = cache(estabelecimentos)
            estabelecimentos['Categoria'] = estabelecimentos['Tipo'].apply(categorizar_estabelecimento)

            # Filtrar estabelecimentos com base nos toggles
            categorias_selecionadas = []
            if toggle_comercio_servicos:
                categorias_selecionadas.append('Comércio e Serviços')
            if toggle_educacao_e_saude:
                categorias_selecionadas.append('Educação e Saúde')
            if toggle_feiras_livres:
                categorias_selecionadas.append('Feira Livre')

            estabelecimentos = estabelecimentos[estabelecimentos['Categoria'].isin(categorias_selecionadas)]

            # Filtro de distância
            #distance = st.slider('Distância de estabelecimentos para analisar (m)', 100, 2000, 500, 100)
            #distance = distance / 1000


distance = 2
### MAIN SECTION ###
col1, col2 = st.columns([2,1])

## COL1 SERÁ PARA O MAPA ##
with col1:
    event = None
    if distritos_filtrados:
        # Filtrar dados pelo distrito selecionado
        gdf_filtered = gdf_filtered[gdf_filtered['NOME_DIST'].isin([distritos_filtrados])]
        gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin([distritos_filtrados])]


        if exibir_vendas:
            # Separar dados em vendidos e não vendidos
            gdf_nao_vendidos = gdf_filtered[gdf_filtered['venda'] == False]
            gdf_vendidos = gdf_filtered[gdf_filtered['venda'] == True]

            # Plotar terrenos não vendidos
            fig = plot_zones_with_colors(
                gdf_nao_vendidos, 
                mapbox_style=mapbox_style,
                color_var="tipo",
                hover_data=['zl_zona','SQL'],
                color_discrete_map=COLOR_MAP
            )
            # Adicionar terrenos vendidos se existirem
            if not gdf_vendidos.empty:
                fig.add_trace(
                    plot_zones_with_colors(
                        gdf_vendidos,
                        mapbox_style=mapbox_style,
                        color_var="venda",
                        hover_data=[
                            'zl_zona', 'SQL', 'digito SQL',
                            'Nome do Logradouro', 'Número', 'Bairro',
                            'Cartório de Registro', 'dados de vendas'
                        ],
                        color_discrete_map={True: 'red', False: 'red'}).data[0])
        else:
            # Plotar todos os terrenos sem distinção de venda
            fig = plot_zones_with_colors(
                gdf_filtered,
                mapbox_style=mapbox_style,
                color_var="tipo",
                hover_data=['zl_zona','SQL'],
                color_discrete_map=COLOR_MAP)

        ## Adicionar os limites dos distritos ##
        fig = plot_borders(gdf_distritos_f, fig, mapbox_style=mapbox_style)
        # map height
        fig.update_layout(height=600)

        ## Adicionar os estabelecimentos ##
        if (toggle_comercio_servicos or toggle_educacao_e_saude or toggle_feiras_livres) and estabelecimentos is not None and not estabelecimentos.empty:
            # Plotar estabelecimentos por Tipo, mantendo as cores
            for tipo, dados_tipo in estabelecimentos.groupby('Tipo'):
                size = 16 if tipo == "Shopping Center" or tipo == "Feira Livre" else 8
                fig.add_trace(go.Scattermapbox(
                    lat=dados_tipo['Latitude'],
                    lon=dados_tipo['Longitude'],
                    mode='markers',
                    marker=dict(size=size, color=COLOR_DICT_ESTABELECIMENTOS.get(tipo, 'gray'), opacity=0.8),
                    name=tipo,
                    hovertemplate="""
                        <b>Nome:</b> %{customdata[0]}<br>
                        <b>Tipo:</b> %{customdata[1]}<br>
                        <b>Endereço:</b> %{customdata[2]}<br>
                        <extra></extra>
                    """,
                    customdata=np.column_stack((
                        dados_tipo['Nome'],
                        dados_tipo['Tipo'],
                        dados_tipo['Endereço']
                    )),
                    selected=dict(marker=dict(opacity=0.9)),
                    unselected=dict(marker=dict(opacity=0.9)),
                ))

        # Plotar pontos/linhas de mobilidade
        if mobility_selected:
            for tipo in mobility_selected:
                df_mobility = mobilidade.get(tipo)
                if df_mobility is not None and not df_mobility.empty:
                    if tipo in LINE_MOBILITIES:
                        if tipo in ['Linha metro projeto', 'Linha metro'] and 'lmt_nome' in df_mobility.columns:
                            # Agrupando por lmt_nome para diferenciar as linhas
                            for nome_linha, grupo in df_mobility.groupby('lmt_nome'):
                                cor_linha = LINE_COLORS.get(nome_linha.upper(), 'blue')

                                # Verifica se é "Linha metro projeto" para alterar o estilo da linha
                                line_style = dict(color=cor_linha, width=4)
                                if tipo == 'Linha metro projeto':
                                    line_style['dash'] = 'dot'

                                # Extraindo coordenadas para plotagem
                                full_lats = []
                                full_lons = []
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
                                    hoverinfo='text'
                                ))
                        else:
                            # Outras linhas em LINE_MOBILITIES (como 'Ferrovia mdc', 'Linha trem', etc.)
                            default_color = COLOR_DICT_MOBILITY.get(tipo, 'blue')
                            full_lats = []
                            full_lons = []
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
                                line=dict(color=default_color, width=4),
                                name=tipo,
                                text=tipo,
                                hoverinfo='text'
                            ))
                    else:
                        # Caso não seja uma linha, plotar como ponto
                        point_size = 8  # Tamanho padrão dos pontos
                        if tipo == 'Estacao de Metro':  # Verifica se é 'Estacao de metro'
                            point_size = 16  # Define o tamanho específico para 'Estacao de metro'
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

        # Adicionar camada de favelas se o toggle estiver ativado ##
        if mostrar_favelas:
            fig.add_trace(go.Choroplethmapbox(
                geojson=gdf_favela.geometry.__geo_interface__,  
                locations=gdf_favela.index,
                z=[1] * len(gdf_favela),
                colorscale=[[0, 'rgba(255,165,0,0.5)'], [1, 'rgba(255,165,0,0.5)']], 
                showscale=False,
                name='Favelas',  # Nome que aparecerá na legenda
                hoverinfo='text',
                text=gdf_favela[['NOME', 'AREA_m²']].apply(lambda x: f"Nome: {x['NOME']}<br>Área: {x['AREA_m²']:.1f}m²", axis=1),
                showlegend=True  # Força a exibição na legenda
            ))
        # Adicionar camada de áreas inundáveis se o toggle estiver ativado
        if mostrar_inundavel:
            fig.add_trace(go.Choroplethmapbox(
                geojson=gdf_inundavel.geometry.__geo_interface__,  # Usando a geometria de áreas inundáveis
                locations=gdf_inundavel.index,  # Índices do GeoDataFrame
                z=[1] * len(gdf_inundavel),  # Definindo uma cor única para as áreas inundáveis
                colorscale=[[0, 'rgba(0,0,255,0.5)'], [1, 'rgba(0,0,255,0.5)']],  # Usando azul claro para as áreas inundáveis
                showscale=False,  # Não mostrar escala de cor
                name='Áreas Inundáveis',  # Nome que aparecerá na legenda
                showlegend=True  # Força a exibição na legenda
            ))

        # Add a legend
        fig.update_layout(
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.84,
                bgcolor="rgba(10, 10, 20, 0.6)",  # Fundo semi-transparente
                bordercolor="rgba(0, 0, 0, 0.3)",    # Borda suave
                borderwidth=1,
                title="",
            )
        )

        # Display the map with selection enabled
        event = st.plotly_chart(fig, on_select="rerun", selection_mode=["points", "box", "lasso"], id="map_main")

    ## COL2 SERÁ PARA ANÁLISES ##
    if event:
        with col2:
            sel_lote, sel_estab, sel_mob = get_dfs_from_selected_points(event) ## get_dfs_from_selected_points retorna 3 dfs e está no arquivo principal.py

            st.write("Lotes: ", len(sel_lote))
            st.write("Estabelecimentos: ", len(sel_estab))
            st.write("Mobilidade: ", len(sel_mob))
            st.write("Área Selecionada:", f"{sel_lote['Area'].sum():.1f} m²")
                    

            ## ANALISES ##
            # Bool to check if estabelecimentos are available
            has_estabelecimentos = (toggle_comercio_servicos or toggle_educacao_e_saude) and estabelecimentos is not None and not estabelecimentos.empty
            has_mobility_points = filtered_mobility_points is not None and not filtered_mobility_points.empty

            if len(sel_lote) == 0:
                st.write("Nenhum terreno foi selecionado.")
            else:
                map_selection_df = sel_lote[['SQL', 'Latitude', 'Longitude', 'Zoneamento']]
                # Filtrar pontos de mobilidade próximos aos terrenos selecionados
                if mobility_selected and map_selection_df is not None and not map_selection_df.empty:
                    filtered_mobility_points = filter_mobility_points_by_distance(mobilidade_analisavel, map_selection_df, distance)


                ## THIS ANALYSIS SHOULD IMPROVE - ASK VAGNER ##
                # Análise de Pontos de Mobilidade
                # Relatório de Pontos de Mobilidade Próximos - Mais Próximos por Tipo
                if filtered_mobility_points is not None and not filtered_mobility_points.empty:
                    #st.header("Pontos de Mobilidade")
                    mob_mais_proximos = filtered_mobility_points.loc[filtered_mobility_points.groupby('Tipo')['Distancia (m)'].idxmin()]
                    with st.expander('Pontos de Mobilidade',expanded=True):
                        st.dataframe(mob_mais_proximos.set_index('Tipo')['Distancia (m)'])
                
                # Análise de Estabelecimentos
                if has_estabelecimentos:
                    filtered_estabelecimentos = filter_estabelecimentos_by_distance(estabelecimentos, map_selection_df, distance)
                    if not filtered_estabelecimentos.empty:
                        estab_mais_proximos = filtered_estabelecimentos.loc[filtered_estabelecimentos.groupby('Tipo')['Distancia (m)'].idxmin()]
                        with st.expander('Estabelecimentos',expanded=True):
                            st.dataframe(estab_mais_proximos.set_index('Tipo')['Distancia (m)'])

                    # Gera a tabela de pontuacao do terreno
                    tabela_pontos, score = gerar_pontuacao(mob_mais_proximos= mob_mais_proximos, estab_mais_proximos= estab_mais_proximos)
                    exibir_score(score)
                    with st.expander('Mostrar detalhadas'):
                        st.dataframe(tabela_pontos.set_index("Categoria"))

if distritos_filtrados:
    with col1:
        with st.expander('Renda por faixa de distrito'):
            df_melted = pd.melt(df_domicilios, id_vars=['Distritos'], var_name='Faixa de Renda', value_name='Quantidade')

        # Agora a tabela já está no formato desejado
        # Vamos usar pivot_table para rearranjar a tabela
            df_pivot = df_melted.pivot(index='Faixa de Renda', columns='Distritos', values='Quantidade')

        # Exibindo o DataFrame pivotado
            st.write(df_pivot[distritos_filtrados])
