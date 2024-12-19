import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
from pages.utils.constants import DASHBOARD_COLORS

QT_BINS = 5

def criar_graficos_dashboard(df):
    # Cálculos iniciais
    df['VGV'] = df['(VMU)Preço de venda da unidade atualizado CUB'] * df['Nº Total de Unidades']
    
    # Criar bins para área total e adicionar os ranges na descrição
    area_bins = pd.qcut(df['Área Total'], q=QT_BINS, retbins=True)
    df['Area_Bins'] = pd.qcut(df['Área Total'], q=QT_BINS, labels=[
        f'{area_bins[1][i]:.0f}-{area_bins[1][i+1]:.0f}m²' 
        for i in range(QT_BINS)
    ])
    
    # Criar bins para tickets e adicionar os ranges na descrição (em milhares)
    ticket_bins = pd.qcut(df['(VMU)Preço de venda da unidade atualizado CUB'], q=QT_BINS, retbins=True)
    df['Ticket_Bins'] = pd.qcut(df['(VMU)Preço de venda da unidade atualizado CUB'], q=QT_BINS, labels=[
        f'R${ticket_bins[1][i]/1000:.0f}K-R${ticket_bins[1][i+1]/1000:.0f}K' 
        for i in range(QT_BINS)
    ])
    
    # Extrair o ano do lançamento
    df['Ano'] = pd.to_datetime(df['Data Lançamento']).dt.year

    # Função auxiliar para criar gráfico empilhado com linha de VSO
    def criar_grafico_empilhado(dados, x_col):
        # Dicionário para mapear os nomes das colunas
        nomes_colunas = {
            'Area_Bins': 'Área',
            'Unidade': 'Tipologia',
            'Ticket_Bins': 'Ticket'
        }
        
        # Obter o título correto
        titulo = nomes_colunas.get(x_col, x_col)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Adicionar barra de total (cinza)
        fig.add_trace(
            go.Bar(
                name='Total',
                x=dados[x_col],
                y=dados['Nº Total de Unidades'],
                marker_color='#95a5a6',  # Cinza
                text=dados['Nº Total de Unidades'],
                textposition='auto',
            ),
            secondary_y=False
        )
        
        # Adicionar barra de vendidas (azul)
        fig.add_trace(
            go.Bar(
                name='Vendidas',
                x=dados[x_col],
                y=dados['Unidades Vendidas'],
                marker_color='#3498db',  # Azul
                text=dados['Unidades Vendidas'],
                textposition='auto',
            ),
            secondary_y=False
        )
        
        # Adicionar barra de estoque (vermelho)
        fig.add_trace(
            go.Bar(
                name='Estoque',
                x=dados[x_col],
                y=dados['Qtd em Estoque'],
                marker_color='#e74c3c',  # Vermelho
                text=dados['Qtd em Estoque'],
                textposition='auto',
            ),
            secondary_y=False
        )
        
        
        # Adicionar linha de VSO
        fig.add_trace(
            go.Scatter(
                name='VSO (%)',
                x=dados[x_col],
                y=dados['VSO'],
                mode='lines+markers',
                line=dict(color='#2c3e50'),  # Linha escura
                text=dados['VSO'].apply(lambda x: f'{x:.1f}%'),
                textposition='top center',
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            barmode='group',  # Agrupa as barras lado a lado
            title=f'Unidades por {titulo} com VSO',
            showlegend=True,
            margin=dict(t=100),  # Aumenta a margem superior para acomodar a legenda
            legend=dict(
                yanchor="bottom",
                y=1.02,  # Posiciona a legenda acima do gráfico
                xanchor="center",
                x=0.5,
                orientation="h",  # Orientação horizontal
                bgcolor='rgba(0,0,0,0)'  # Fundo transparente
            )
        )
        
        # Adicione esta condição para formatar o eixo x quando for 'Ano'
        if x_col == 'Ano':
            fig.update_xaxes(tickformat='d')  # 'd' força números inteiros sem vírgulas
        
        fig.update_yaxes(title_text="Quantidade de Unidades", secondary_y=False)
        fig.update_yaxes(title_text="VSO (%)", secondary_y=True)
        
        return fig

    # Gráficos
    figs = []
    
    # 1. Por Empreendimento
    df_emp = df.groupby('Empreendimento').agg({
        'Unidades Vendidas': 'sum',
        'Qtd em Estoque': 'sum',
        'Nº Total de Unidades': 'sum'
    }).reset_index()
    df_emp['VSO'] = (df_emp['Unidades Vendidas'] / df_emp['Nº Total de Unidades'] * 100)
    figs.append(criar_grafico_empilhado(df_emp, 'Empreendimento'))

    # 2. Por Área
    df_area = df.groupby('Area_Bins').agg({
        'Unidades Vendidas': 'sum',
        'Qtd em Estoque': 'sum',
        'Nº Total de Unidades': 'sum'
    }).reset_index()
    df_area['VSO'] = (df_area['Unidades Vendidas'] / df_area['Nº Total de Unidades'] * 100)
    figs.append(criar_grafico_empilhado(df_area, 'Area_Bins'))

    # 3. Por Unidade (Unidade)
    df_unid = df.groupby('Unidade').agg({
        'Unidades Vendidas': 'sum',
        'Qtd em Estoque': 'sum',
        'Nº Total de Unidades': 'sum'
    }).reset_index()
    df_unid['VSO'] = (df_unid['Unidades Vendidas'] / df_unid['Nº Total de Unidades'] * 100)
    figs.append(criar_grafico_empilhado(df_unid, 'Unidade'))

    # 4. Por Ticket
    df_ticket = df.groupby('Ticket_Bins').agg({
        'Unidades Vendidas': 'sum',
        'Qtd em Estoque': 'sum',
        'Nº Total de Unidades': 'sum'
    }).reset_index()
    df_ticket['VSO'] = (df_ticket['Unidades Vendidas'] / df_ticket['Nº Total de Unidades'] * 100)
    figs.append(criar_grafico_empilhado(df_ticket, 'Ticket_Bins'))

    # 5. Por Ano (substituindo Idade_Bins)
    df_ano = df.groupby('Ano').agg({
        'Unidades Vendidas': 'sum',
        'Qtd em Estoque': 'sum',
        'Nº Total de Unidades': 'sum'
    }).reset_index()
    df_ano['VSO'] = (df_ano['Unidades Vendidas'] / df_ano['Nº Total de Unidades'] * 100)
    figs.append(criar_grafico_empilhado(df_ano, 'Ano'))

    return figs

def gerar_html_dashboard(df, fig1, fig2, fig3, fig4, fig5):
    total_lancado = int(df['Nº Total de Unidades'].sum())
    total_vendido = int(df['Unidades Vendidas'].sum())
    total_estoque = int(df['Qtd em Estoque'].sum()) 
    vso_total = (df['Unidades Vendidas'].sum() / df['Nº Total de Unidades'].sum() * 100)
    
    html = f"""
    <html>
        <head>
            <title>Dashboard de Análise de Mercado</title>
        </head>
        <body>
            <h1>Dashboard de Análise de Mercado</h1>
            <div style="display: flex; justify-content: space-between; margin: 20px 0;">
                <div>Total Lançado: {total_lancado:,}</div>
                <div>Total Vendido: {total_vendido:,}</div>
                <div>Total em Estoque: {total_estoque:,}</div>
                <div>VSO Médio: {vso_total:.1f}%</div>
            </div>
            {fig1.to_html(full_html=False, include_plotlyjs='cdn')}
            {fig2.to_html(full_html=False, include_plotlyjs='cdn')}
            {fig3.to_html(full_html=False, include_plotlyjs='cdn')}
            {fig4.to_html(full_html=False, include_plotlyjs='cdn')}
            {fig5.to_html(full_html=False, include_plotlyjs='cdn')}
        </body>
    </html>
    """
    return html

def mostrar_dashboard(df):
    if df is None or df.empty:
        st.warning("Nenhum dado disponível para análise")
        return
    
    if df["RGI"].unique().size == 1:
        st.warning("Não é possível gerar o dashboard com apenas um RGI")
        return
        
    st.title("Dashboard de Análise de Mercado")
    
    # Sidebar com filtros
    with st.sidebar:
        st.header("Filtros")
        
        # Filtro de Incorporadora
        incorporadoras = sorted(df['Grupo Incorporador Apelido'].unique())
        incorporadoras_selecionadas = st.multiselect(
            'Incorporadora',
            incorporadoras,
            default=incorporadoras
        )
        
        # Filtro de Data Lançamento
        min_data = pd.to_datetime(df['Data Lançamento']).min()
        max_data = pd.to_datetime(df['Data Lançamento']).max()
        data_range = st.date_input(
            'Período de Lançamento',
            value=(min_data, max_data),
            min_value=min_data,
            max_value=max_data
        )
        
        # Filtros numéricos com slider
        col1, col2 = st.columns(2)
        with col1:
            vso_range = st.slider(
                'VSO (%)',
                0.0,
                100.0,
                (0.0, 100.0),
                step=1.0
            )
            
            total_lancado_range = st.slider(
                'Total Lançado',
                int(df['Nº Total de Unidades'].min()),
                int(df['Nº Total de Unidades'].max()),
                (int(df['Nº Total de Unidades'].min()), int(df['Nº Total de Unidades'].max()))
            )
        
        with col2:
            estoque_range = st.slider(
                'Estoque',
                int(df['Qtd em Estoque'].min()),
                int(df['Qtd em Estoque'].max()),
                (int(df['Qtd em Estoque'].min()), int(df['Qtd em Estoque'].max()))
            )
            
            total_vendido_range = st.slider(
                'Total Vendido',
                int(df['Unidades Vendidas'].min()),
                int(df['Unidades Vendidas'].max()),
                (int(df['Unidades Vendidas'].min()), int(df['Unidades Vendidas'].max()))
            )
    
    # Aplicar filtros
    mask = (
        df['Grupo Incorporador Apelido'].isin(incorporadoras_selecionadas) &
        (pd.to_datetime(df['Data Lançamento']).dt.date >= data_range[0]) &
        (pd.to_datetime(df['Data Lançamento']).dt.date <= data_range[1]) &
        (df['Nº Total de Unidades'] >= total_lancado_range[0]) &
        (df['Nº Total de Unidades'] <= total_lancado_range[1]) &
        (df['Qtd em Estoque'] >= estoque_range[0]) &
        (df['Qtd em Estoque'] <= estoque_range[1]) &
        (df['Unidades Vendidas'] >= total_vendido_range[0]) &
        (df['Unidades Vendidas'] <= total_vendido_range[1])
    )
    
    # Calcular VSO para filtro
    df['VSO'] = (df['Unidades Vendidas'] / df['Nº Total de Unidades'] * 100)
    mask = mask & (df['VSO'] >= vso_range[0]) & (df['VSO'] <= vso_range[1])
    
    # Aplicar máscara aos dados
    df_filtrado = df[mask]
    
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados")
        return
    
    if df_filtrado["RGI"].unique().size == 1:
        st.warning("Não é possível gerar o dashboard com apenas um RGI")
        return

    # Métricas gerais
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Empreendimentos", f"{df_filtrado['RGI'].nunique()}")
    with col2:
        st.metric("TT Unidades", f"{int(df_filtrado['Nº Total de Unidades'].sum()):,}")
    with col3:
        st.metric("Vendas", f"{int(df_filtrado['Unidades Vendidas'].sum()):,}")
    with col4:
        vgv_total = (df_filtrado['(VMU)Preço de venda da unidade atualizado CUB'] * df_filtrado['Nº Total de Unidades']).sum()
        st.metric("VGV", f"R$ {vgv_total/1e6:,.1f}M")
    with col5:
        vso_total = (df_filtrado['Unidades Vendidas'].sum() / df_filtrado['Nº Total de Unidades'].sum() * 100)
        st.metric("VSO", f"{vso_total:.1f}%")
    with col6:
        st.metric("Estoque", f"{int(df_filtrado['Qtd em Estoque'].sum()):,}")

    # Gráficos
    figs = criar_graficos_dashboard(df_filtrado)
    
    # Exibe os gráficos em layout personalizado
    # Primeira linha: Ticket médio (1/3) e Empreendimentos (2/3)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(figs[0], use_container_width=True)  # Gráfico de Empreendimentos
    with col2:
        st.plotly_chart(figs[3], use_container_width=True)  # Gráfico de Ticket

    # Segunda linha: Área, Unidade e Ano em colunas iguais
    col3, col4, col5 = st.columns(3)
    with col3:
        st.plotly_chart(figs[1], use_container_width=True)  # Gráfico de Área
    with col4:
        st.plotly_chart(figs[2], use_container_width=True)  # Gráfico de Unidade
    with col5:
        st.plotly_chart(figs[4], use_container_width=True)  # Gráfico de Ano
    return figs, df_filtrado

if 'dashboard_data' not in st.session_state:
    st.warning("Por favor, selecione os dados na página principal primeiro.")
else:
    figs, df_filtrado = mostrar_dashboard(st.session_state.dashboard_data)

    with st.expander('Exportar'):
        # Tabela detalhada
        st.subheader("Dados Detalhados")
        st.dataframe(df_filtrado)

        # Export options
        col2_1, col2_2, col2_3, col2_4 = st.columns([1, 1, 1, 1])
        # Excel export
        buffer_excel = BytesIO()
        st.session_state.dashboard_data.to_excel(buffer_excel, index=False)
        buffer_excel.seek(0)
        
        # HTML e PDF export
        html_content = gerar_html_dashboard(st.session_state.dashboard_data, figs[0], figs[1], figs[2], figs[3], figs[4])
        
        
        with col2_2:
            st.download_button(
                label="Download HTML",
                data=html_content.encode(),
                file_name="dashboard_de_análise_de_mercado.html",
                mime="text/html",
                use_container_width=True
            )
        
        with col2_3:
            st.download_button(
                label="Download Excel",
                data=buffer_excel,
                file_name=f"dashboard_de_análise_de_mercado.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )