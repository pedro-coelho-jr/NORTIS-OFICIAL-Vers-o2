# external imports
import streamlit as st
import geopandas as gpd
import pandas as pd
import os
import plotly.express as px
from unidecode import unidecode
import re

# internal imports
from plot.plot_zones import plot_zones_with_colors
from plot.Distritos import plot_borders
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio
from pages.utils.principal import get_dfs_from_selected_points, filter_estabelecimentos_by_distance, filter_mobility_points_by_distance
from pages.utils.utils import load_geojson, convert_to_int, load_all_xlsx_in_directory, categorizar_estabelecimento
from pages.utils.constants import (
    DISTRITOS_CENTRO, DISTRITOS_LESTE, DISTRITOS_NORTE, DISTRITOS_OESTE, DISTRITOS_SUL,
    COLOR_MAP, COLOR_DICT_ESTABELECIMENTOS, COLOR_DICT_MOBILITY,
)

### PAGE CONFIG ###
st.set_page_config(layout="wide")


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

@st.cache_data
def carregar_dados_ITBI(directory_path):
    transacoes = pd.read_csv(directory_path,
                            dtype={
                                'SQL': 'str',
                                'Nome do Logradouro': 'str',
                                'Número': 'str',
                                'Complemento': 'str',
                                'Bairro': 'str',
                                'CEP':'str',
                                'Valor de Transação (declarado pelo contribuinte)': 'float32',
                                'Valor Financiado': 'float32',
                                'Cartório de Registro': 'str',
                                'Matrícula do Imóvel': 'str',
                                'ultimo digito': 'str',
                                'Proporção Transmitida (%)':'float32',
                                'Data de Transação':'str',
                                'Natureza de Transação':'str',
                                'NOME_DIST':'str',
                                'zl_zona':'str'
                                })
    transacoes['Matrícula do Imóvel'] = transacoes['Matrícula do Imóvel'].apply(lambda x: x.split('.')[0])
    transacoes['CEP'] = transacoes['CEP'].apply(lambda x: x.split('.')[0])
    transacoes['Número'] = transacoes['Número'].apply(lambda x: x.split('.')[0])
    transacoes['Data de Transação'] = pd.to_datetime(transacoes['Data de Transação'], errors='coerce')
    return transacoes

@st.cache_data
def cache(dataframe):
    return dataframe
### STARTING DATA SECTION ###
distritos = encontrar_arquivo('distritos.geojson')
sp_distritos = load_geojson(distritos)

tabela_ITBI = encontrar_arquivo('tabela_filtros_ITBI_finalizada.csv')
dados_ITBI = pd.read_csv(tabela_ITBI, dtype={'SQL': 'str'})
dados_ITBI['Data de Transação'] = pd.to_datetime(dados_ITBI['Data de Transação'], errors='coerce')
dados_ITBI = carregar_dados_ITBI(encontrar_arquivo('dados_ITBI.csv'))

licencas = cache(pd.read_excel(encontrar_arquivo('licencas e alvaras.xlsx')))
licencas['combinado'] = licencas['SQL_Incra'].str.replace(r'[.-]', '', regex=True)

# Initialize map_selection_df
st.session_state.map_selection_df = pd.DataFrame()
st.session_state.event = None

distritos_filtrados = gpd.GeoDataFrame()
dados_ITBI_filtrados = pd.DataFrame()
### SIDEBAR SECTION ###
with st.sidebar:
    distritos_selecionados = st.multiselect('selecione os distritos', sorted(sp_distritos['NOME_DIST'].unique()))

        # Escolha do tipo de mapa
    distritos_shapefiles = []
    if distritos_selecionados:
        for distrito_selecionado in distritos_selecionados:
            # Encontrar o diretório para cada zona
            arquivo_distrito = encontrar_diretorio(distrito_selecionado)
            # Carregar os dados correspondentes
            gdf_ = load_zone_geojson_or_shp(arquivo_distrito)
            # Adicionar ao lista de dados filtrados
            distritos_shapefiles.append(gdf_)

        distritos_filtrados = gpd.GeoDataFrame(pd.concat(distritos_shapefiles,ignore_index=True))

        dados_ITBI = dados_ITBI[dados_ITBI['NOME_DIST'].isin(distritos_selecionados)]



        def extrair_numero(natureza):
            match = re.match(r'(\d+)', natureza)  # Extrai a parte numérica antes do ponto
            return int(match.group(1)) if match else float('nan')

        opcoes_de_natureza = sorted(dados_ITBI['Natureza de Transação'].unique(), key=extrair_numero)
        # Filtrando por Natureza de Transação
        natureza = st.multiselect('Selecione a Natureza de Transação', options=['Todos'] + opcoes_de_natureza)

        if natureza:  # Verifica se alguma natureza foi selecionada
            if 'Todos' not in natureza:
                dados_ITBI = dados_ITBI[dados_ITBI['Natureza de Transação'].isin(natureza)]
        else:
            st.warning("Selecione pelo menos uma Natureza de Transação.")
            dados_ITBI = pd.DataFrame()  # Limpa os dados caso o filtro de natureza não seja válido

        if not dados_ITBI.empty:  # Só aplica o próximo filtro se o DataFrame não estiver vazio
            # Filtrando por Proporção Transmitida (%)
            proporcao = st.slider(
                'Selecione o intervalo de Proporção Transmitida (%)',
                min_value=int(dados_ITBI['Proporção Transmitida (%)'].min()),
                max_value=int(dados_ITBI['Proporção Transmitida (%)'].max()),
                value=(int(dados_ITBI['Proporção Transmitida (%)'].min()), int(dados_ITBI['Proporção Transmitida (%)'].max()))
            )

            dados_ITBI = dados_ITBI[
                dados_ITBI['Proporção Transmitida (%)'].between(proporcao[0], proporcao[1])
            ]
        else:
            dados_ITBI = pd.DataFrame()  # Se o filtro anterior não gerar dados, não aplica os seguintes
        if not dados_ITBI.empty:
            # Normalizando os valores de 'Data de Transação' para garantir que estejam no formato correto
            dados_ITBI['Data de Transação'] = pd.to_datetime(dados_ITBI['Data de Transação']).dt.normalize()

            # Obtendo o intervalo de datas do DataFrame
            start_date = dados_ITBI['Data de Transação'].min().date()  # Data mínima
            end_date = dados_ITBI['Data de Transação'].max().date()    # Data máxima

            # Criando o slider de intervalo de datas
            data_inicio, data_fim = st.slider(
                'Selecione o intervalo de datas',
                min_value=start_date,    # data mínima do slider
                max_value=end_date,      # data máxima do slider
                value=(start_date, end_date),  # valores inicial e final padrão
                format="DD/MM/YYYY"  # Formato de exibição das datas
            )

            # Normalizando as datas selecionadas pelo slider
            data_inicio = pd.to_datetime(data_inicio)
            data_fim = pd.to_datetime(data_fim)

            # Filtrando os dados com base no intervalo de datas selecionado
            dados_ITBI = dados_ITBI[
                (dados_ITBI['Data de Transação'] >= data_inicio) &
                (dados_ITBI['Data de Transação'] <= data_fim)
            ]
        else:
            dados_ITBI = pd.DataFrame()  # Se o filtro anterior não gerar dados, não aplica os seguintes
        
        if not dados_ITBI.empty:
            valor = st.slider(
                'Selecione o intervalo de valores de transação',
                min_value=int(dados_ITBI['Valor de Transação (declarado pelo contribuinte)'].min()),
                max_value=int(dados_ITBI['Valor de Transação (declarado pelo contribuinte)'].max()),
                value=(int(dados_ITBI['Valor de Transação (declarado pelo contribuinte)'].min()), int(dados_ITBI['Valor de Transação (declarado pelo contribuinte)'].max()))
           )
        
            dados_ITBI_filtrados = dados_ITBI[
               dados_ITBI['Valor de Transação (declarado pelo contribuinte)'].between(valor[0], valor[1])
            ] 
        else:
            dados_ITBI_filtrados = pd.DataFrame()






### MAIN SECTION ###
#col1, col2 = st.columns([2,1])

## COL1 SERÁ PARA O MAPA ##
#with col1:
event = None
if not distritos_filtrados.empty and not dados_ITBI_filtrados.empty:
    gdf_distritos_f = sp_distritos[sp_distritos['NOME_DIST'].isin(distritos_selecionados)]
    distritos_filtrados = distritos_filtrados[distritos_filtrados['venda'] == True]
    distritos_filtrados = distritos_filtrados[distritos_filtrados['SQL'].isin(dados_ITBI_filtrados['SQL'])]
    
    mapbox_style = st.selectbox('Estilo do Mapa', ['open-street-map', 'carto-positron', 'carto-darkmatter', 'satellite-streets', 'satellite'])
        # Plotar todos os terrenos sem distinção de venda
    fig = plot_zones_with_colors(
        distritos_filtrados,
        mapbox_style=mapbox_style,
        color_var="tipo",
        hover_data=['zl_zona', 'SQL', 'digito SQL',
                            'Nome do Logradouro', 'Número', 'Bairro',
                            'Cartório de Registro', 'dados de vendas'],
        color_discrete_map={'lote': 'red', 'condominio': 'blue'})

    ## Adicionar os limites dos distritos ##
    fig = plot_borders(gdf_distritos_f, fig, mapbox_style=mapbox_style)
    # map height
    fig.update_layout(height=600)
    event = st.plotly_chart(fig, on_select="rerun", selection_mode=["points", "box", "lasso"], id="map_main")


def get_df_from_selected_point(event):
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

    return sel_lote

#with col2:
with st.expander("Clique para exibir informações detalhadas"):
    if event:
        # Renomeando as colunas
        novo_nome_colunas = {
            'Nome do Logradouro': 'Logradouro',
            'Valor de Transação (declarado pelo contribuinte)': 'Valor',
            'Proporção Transmitida (%)':'% Transmitida',
            'Natureza de Transação':'Natureza',
            'Valor Financiado':'Financiado',
            'Matrícula do Imóvel': 'Matrícula',
            'Data de Transação':'Data',
        }
        sel_lote = get_df_from_selected_point(event)
        dados_cadastrais = dados_ITBI_filtrados[dados_ITBI_filtrados['SQL'].isin(sel_lote['SQL'])][['SQL',
                                                                                                    'Matrícula do Imóvel',
                                                                                                    'Nome do Logradouro',
                                                                                                    'Número',
                                                                                                    'Complemento',
                                                                                                    'Bairro',
                                                                                                    'CEP',
                                                                                                    'NOME_DIST',
                                                                                                    'zl_zona',
                                                                                                    'Área do Terreno (m2)',
                                                                                                    'Testada (m)',
                                                                                                    'Área Construída (m2)']]
        dados_cadastrais = dados_cadastrais.rename(columns = {'NOME_DIST':'Distrito','zl_zona':'Zona','Matrícula do Imóvel':'Matrícula'}).drop_duplicates(subset=['SQL'])
        dados_de_vendas = dados_ITBI_filtrados[dados_ITBI_filtrados['SQL'].isin(sel_lote['SQL'])][['SQL',
                                                                                                    'Data de Transação',
                                                                                                    'Matrícula do Imóvel',
                                                                                                    'Valor de Transação (declarado pelo contribuinte)',
                                                                                                    'Tipo de Financiamento',
                                                                                                    'Valor Financiado',
                                                                                                    'Cartório de Registro']]
        
        dados_de_vendas['Data de Transação'] = pd.to_datetime(dados_de_vendas['Data de Transação']).dt.strftime('%d/%m/%Y')
        dados_de_vendas = dados_de_vendas.rename(columns = {'Valor de Transação (declarado pelo contribuinte)':'Valor de Transação'})
        st.dataframe(dados_cadastrais.set_index('SQL'))
        st.dataframe(dados_de_vendas.set_index('SQL'))

        dados_relacionais = pd.merge(dados_cadastrais['SQL'], distritos_filtrados[['SQL', 'digito SQL']], on='SQL', how='left')

        # Criando a coluna 'combinado' com a soma
        dados_relacionais['combinado'] = dados_relacionais['SQL'] + dados_relacionais['digito SQL'].fillna('')
        dados_licencas = licencas[licencas['combinado'].isin(dados_relacionais['combinado'])]
        dados_licencas['Data autuação'] = pd.to_datetime(dados_licencas['Data autuação'], errors='coerce', dayfirst=True)
        dados_licencas['Data autuação'] = dados_licencas['Data autuação'].dt.strftime('%d/%m/%Y')
        dados_licencas['Aprovação'] = pd.to_datetime(dados_licencas['Aprovação'], errors='coerce', dayfirst=True)
        dados_licencas['Aprovação'] = dados_licencas['Aprovação'].dt.strftime('%d/%m/%Y')
        st.dataframe(dados_licencas.set_index('SQL_Incra'))








if not distritos_filtrados.empty and not dados_ITBI_filtrados.empty:
    dados_ITBI_filtrados['Mês'] = dados_ITBI_filtrados['Data de Transação'].dt.to_period('M').astype(str)  # Exemplo: 2023-01
    dados_ITBI_filtrados['Ano'] = dados_ITBI_filtrados['Data de Transação'].dt.year  # Exemplo: 2023

    # Interface para seleção de granularidade
    granularidade = st.radio("Escolha a granularidade da análise:", ["Mensal", "Anual"])

    if granularidade == "Mensal":
        # Evolução mensal de transações
        evolucao_mensal = dados_ITBI_filtrados.groupby('Mês')['Valor de Transação (declarado pelo contribuinte)'].sum().reset_index()
        evolucao_mensal['Mês'] = evolucao_mensal['Mês'].astype(str)

        # Gráfico mensal
        fig_evolucao = px.line(
            evolucao_mensal,
            x="Mês",
            y="Valor de Transação (declarado pelo contribuinte)",
            title="Evolução Mensal do Valor Total das Transações",
            labels={"Mês": "Mês", "Valor de Transação (declarado pelo contribuinte)": "Valor Total (R$)"}
        )
        #fig_evolucao.update_layout(
        #    xaxis=dict(tickmode="array",  # Exibir apenas os valores selecionados no eixo X
        #        tickvals=evolucao_mensal['Mês'],  # Exibe todos os meses
        #        tickangle=45        # Rotacionar os rótulos para melhor visualização
        #        ))
        st.plotly_chart(fig_evolucao)

    elif granularidade == "Anual":
        # Evolução anual de transações
        evolucao_anual = dados_ITBI_filtrados.groupby('Ano')['Valor de Transação (declarado pelo contribuinte)'].sum().reset_index()

        # Gráfico anual
        fig_evolucao = px.bar(
            evolucao_anual,
            x="Ano",
            y="Valor de Transação (declarado pelo contribuinte)",
            title="Evolução Anual do Valor Total das Transações",
            labels={"Ano": "Ano", "Valor de Transação (declarado pelo contribuinte)": "Valor Total (R$)"}
        )
        st.plotly_chart(fig_evolucao)


col3, col4 = st.columns([8,3])
with col3:
    if not distritos_filtrados.empty and not dados_ITBI_filtrados.empty:
        fig_hist = px.histogram(dados_ITBI_filtrados, 
                    x='Valor de Transação (declarado pelo contribuinte)', 
                    nbins=15, 
                    title='Histograma de Transações por Valor', 
                    labels={'Valor de Transação (declarado pelo contribuinte)': 'Valor de Transação (R$)', 
                            'count': 'Frequência'})


        # Personalizar a aparência do gráfico
        fig_hist.update_layout(
            xaxis_title='Valor de Transação (R$)',
            #yaxis_type="log",
            yaxis_title='Frequência',
            bargap=0.2,  # Ajusta o espaço entre as barras
            template='plotly_dark'  # Estilo visual
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig_hist)


st.markdown(
    """
    <style>
    .metric-container {
        display: flex;
        justify-content: center; /* Centraliza horizontalmente */
        align-items: center;    /* Centraliza verticalmente */
        margin-top: 170px;       /* Margem superior */
    }
    .custom-metric {
        background-color: #1f77b4; /* Cor de fundo */
        color: white;             /* Cor do texto */
        border-radius: 10px;      /* Bordas arredondadas */
        padding: 40px;            /* Espaçamento interno */
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2); /* Sombra */
        font-size: 24px;          /* Tamanho da fonte */
        text-align: center;       /* Centralização do texto */
    }
    </style>
    """,
    unsafe_allow_html=True,
)
with col4:
# Calculando o ticket médio
    if not dados_ITBI_filtrados.empty:
        ticket_medio = dados_ITBI_filtrados['Valor de Transação (declarado pelo contribuinte)'].mean()

        # Exibindo o card com CSS customizado
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="custom-metric">
                    <strong>Ticket Médio</strong><br>
                    R$ {ticket_medio:,.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    

        

