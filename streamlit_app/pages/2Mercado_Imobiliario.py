# external imports
import streamlit as st
import pandas as pd
import time
from memory_profiler import profile
import gc
import plotly.graph_objects as go

# internal imports
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio
from services.geocoding import get_coordinates
from services.mercado_imobiliario import get_RGI_close_to_coordinates, get_all_info_RGI
from plot.plot_mercado_imobiliario import plot_mercado_imobiliario
from plot.Distritos import plot_borders
from pages.utils.card_mercado_imob import processar_dataframe
from plot.plot_mobility import plot_mobility
from pages.utils.utils import load_mobility_data
from pages.utils.constants import LINE_MOBILITIES, LINE_COLORS, COLOR_DICT_MOBILITY

MAPBOX_TOKEN = "pk.eyJ1IjoicHJvamV0b2RhZG9zIiwiYSI6ImNtMXdiNjVobTBpa2Eya3BsMnR5OWxsd3AifQ.SGh5qTES1kmMN3VNFzZAwQ"
SAO_PAULO_COORDINATES = (-46.63389, -23.55028)


@profile
def get_cached_coordinates(endereco, token, default_coords):
    coords = get_coordinates(endereco, token, default_coords)
    gc.collect()  # Forçar coleta de lixo
    return coords

@profile
def get_cached_RGI_data(coordenadas, distancia):
    rgis = get_RGI_close_to_coordinates(coordenadas, distancia)
    data = get_all_info_RGI(rgis)
    gc.collect()  # Forçar coleta de lixo
    return data

# Adicionar carregamento dos dados de mobilidade
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


st.set_page_config(layout="wide")

with st.sidebar:
    # Title
    st.title("Página de Análise de Mercado Imobiliário")
    st.subheader("Clique em um ponto para ver os detalhes")
    # Slider
    distancia = st.slider("Distância em metros", min_value=100, max_value=3000, value=2000, step=100)
    # Campo de entrada para o endereço
    endereco = st.text_input("Digite o endereço:")
    # Escolha do tipo de mapa
    mapbox_style = st.sidebar.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter', 'satellite-streets', 'satellite'])
    # Escolha do ano da pesquisa
    ano_pesquisa = st.sidebar.multiselect('Ano da pesquisa', ['2020', '2021', '2022', '2023', '2024'], default=['2020', '2021', '2022', '2023', '2024'])

    # Toggle e seleção de mobilidade
    toggle_mobility = st.toggle("Mostrar Mobilidade", value=False)
    mobility_selected = []
    if toggle_mobility:
        mobility_types = list(mobilidade.keys())
        default_mobility_types = [tipo for tipo in mobility_types if
                              tipo not in ["Linha metro projeto",
                                       "Linha trem projeto",
                                       "Projetos de Estacao de Metro",
                                       "Projetos de Estacao de Trem"]]
        mobility_selected = st.multiselect(
            'Mobilidade',
            mobility_types,
            default=default_mobility_types
        )


if not endereco:
    warning = st.warning("Por favor digite um endereço")
    time.sleep(5)
    warning.empty()
    st.stop()
try:
    coordenadas = get_cached_coordinates(endereco, MAPBOX_TOKEN, SAO_PAULO_COORDINATES)
    success = st.success(f"Coordenadas encontradas: Latitude {coordenadas[0]}, Longitude {coordenadas[1]}")
    time.sleep(5)
    success.empty()
except:
    error = st.error("Não foi possível encontrar as coordenadas para este endereço.")
    time.sleep(5)
    error.empty()
    st.stop()

full_info = get_cached_RGI_data(coordenadas, distancia)

full_info["Soma Estoque"] = full_info.groupby("RGI")["Qtd em Estoque"].transform('sum')

# filter by year
if ano_pesquisa:
    # change to string
    full_info["Ano"] = full_info["Ano"].astype(str)
    full_info = full_info[full_info["Ano"].isin(ano_pesquisa)]

# Mapa
fig = plot_mercado_imobiliario(full_info, color_var="Status", center=(coordenadas[0] - 0.01, coordenadas[1]), dot_color=["blue", "green", "orange", "magenta"], dot_size=15,
                                hover_data=["Empreendimento", "Grupo Incorporador Apelido", "Infraestrutura", "Torres", "Soma Estoque", "RGI"], mapbox_style=mapbox_style)

# Adicionar camadas de mobilidade
if toggle_mobility and mobility_selected:
    fig = plot_mobility(fig, mobility_selected, mobilidade, 
                        LINE_MOBILITIES, LINE_COLORS, COLOR_DICT_MOBILITY)

# Adicionar ponto de pesquisa
fig.add_trace(
    go.Scattermap(
        lat=[coordenadas[0]],
        lon=[coordenadas[1]],
        mode='markers',
        marker=dict(size=25, color='red'),
        name='Ponto de Pesquisa'
    )   
)
# Centralizar o mapa no ponto de pesquisa
fig.update_layout(
    map=dict(
        center=dict(lat=coordenadas[0], lon=coordenadas[1]),
        zoom=14
    )
)

event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode=["points", "box", "lasso"], config={'scrollZoom': True})
points = event.selection["points"] if event else []

# Filtrar pontos selecionados, excluindo o ponto de pesquisa
selected_rgis = []
if points:
    selected_rgis = [point["customdata"][5] for point in points 
                        if point.get("customdata") and len(point["customdata"]) > 5 and point["customdata"][5] is not None]

# Análises
if not full_info.empty:
    # Adicionar seleção de ordenação
    ordem = st.sidebar.selectbox(
        'Ordenar por',
        ['Sem ordenação', 'Estoque (Maior)', 'Estoque (Menor)', 'Ticket (Maior)', 'Ticket (Menor)']
    )

    if event and len(selected_rgis) > 0:
        display_table = full_info[full_info["RGI"].isin(selected_rgis)]
        rgis_sel_2 = selected_rgis
    else: 
        display_table = full_info
        rgis_sel_2 = full_info["RGI"].unique()

        
    # Adicionar botão para o dashboard
    if st.button("Ver Dashboard de Análise", key="dashboard_button"):
        if 'dashboard_data' not in st.session_state:
            st.session_state.dashboard_data = pd.DataFrame()
        
        if event and len(rgis_sel_2) > 0:
            st.session_state.dashboard_data = full_info[full_info["RGI"].isin(rgis_sel_2)]

        # Usar switch_page em vez de redirect
        if st.session_state.dashboard_data.empty:
            st.error("Nenhum RGI selecionado")
        else:
            st.switch_page("pages/4Dashboard_Mercado.py")

    # Aplicar ordenação
    if ordem != 'Sem ordenação':
        rgi_stats = display_table.groupby('RGI').agg({
            'Qtd em Estoque': 'sum',
            '(VMU)Preço de venda da unidade atualizado CUB': 'mean'
        }).reset_index()
        
        if ordem == 'Estoque (Maior)':
            ordem_rgis = rgi_stats.sort_values('Qtd em Estoque', ascending=False)['RGI']
        elif ordem == 'Estoque (Menor)':
            ordem_rgis = rgi_stats.sort_values('Qtd em Estoque', ascending=True)['RGI']
        elif ordem == 'Ticket (Maior)':
            ordem_rgis = rgi_stats.sort_values('(VMU)Preço de venda da unidade atualizado CUB', ascending=False)['RGI']
        else:  # Ticket (Menor)
            ordem_rgis = rgi_stats.sort_values('(VMU)Preço de venda da unidade atualizado CUB', ascending=True)['RGI']
        
        # Reordenar os RGIs para processamento
        ordered_rgis = [rgi for rgi in ordem_rgis if rgi in display_table["RGI"].unique()]
    else:
        ordered_rgis = display_table["RGI"].unique()

    # drop empty columns
    for col in display_table.columns:
        if display_table[col].isna().all():
            display_table = display_table.drop(columns=[col])

    # Mostrar os primeiros 5 cards
    i = 0
    for rgi in ordered_rgis[:5]:
        if i % 3 == 0:
            cols = st.columns(3)
        with cols[i % 3]:
            processar_dataframe(display_table[display_table["RGI"] == rgi])
        i += 1

    # Toggle para mostrar o restante
    if st.toggle("Mostrar tudo (mais que 5)"):
        # Mostrar os cards restantes
        for rgi in ordered_rgis[5:]:
            if i % 3 == 0:
                cols = st.columns(3)
            with cols[i % 3]:
                processar_dataframe(display_table[display_table["RGI"] == rgi])
            i += 1

    # Limpar variáveis grandes que não são mais necessárias
    if 'display_table' in locals():
        del display_table
    gc.collect()