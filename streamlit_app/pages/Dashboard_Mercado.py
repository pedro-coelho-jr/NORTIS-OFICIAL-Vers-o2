import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO

def criar_graficos_dashboard(df):
    # Agrupa os dados por RGI
    df_agrupado = df.groupby(['RGI', 'Empreendimento']).agg({
        'Nº Total de Unidades': 'sum',
        'Unidades Vendidas': 'sum',
        'Qtd em Estoque': 'sum'
    }).reset_index()
    
    # Calcula o VSO
    df_agrupado['VSO'] = (df_agrupado['Unidades Vendidas'] / df_agrupado['Nº Total de Unidades'] * 100).round(2)
    
    # Cria gráfico de barras empilhadas
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        name='Vendidas',
        x=df_agrupado['Empreendimento'],
        y=df_agrupado['Unidades Vendidas'],
        marker_color='green',
        text=df_agrupado['Unidades Vendidas'],
        textposition='auto',
    ))
    fig1.add_trace(go.Bar(
        name='Estoque',
        x=df_agrupado['Empreendimento'],
        y=df_agrupado['Qtd em Estoque'],
        marker_color='red',
        text=df_agrupado['Qtd em Estoque'],
        textposition='auto',
    ))
    fig1.update_layout(
        barmode='stack',
        title='Unidades Vendidas vs Estoque por Empreendimento',
        xaxis_title='Empreendimento',
        yaxis_title='Quantidade de Unidades',
        showlegend=True,
        # Ajustar margem superior para acomodar os labels
        margin=dict(t=50),
        # Configurações uniformes para todos os labels
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    # Faça a legenda ficar em cima do grafico
    fig1.update_layout(legend=dict(yanchor='top', y=0.95, xanchor='left', x=0.05))
    
    # Cria gráfico de VSO
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_agrupado['Empreendimento'],
        y=df_agrupado['VSO'],
        marker_color='blue',
        text=df_agrupado['VSO'].apply(lambda x: f'{x:.1f}%'),
        textposition='auto',
    ))
    fig2.update_layout(
        title='VSO por Empreendimento',
        xaxis_title='Empreendimento',
        yaxis_title='VSO (%)',
        # Ajustar margem superior para acomodar os labels
        margin=dict(t=50),
        # Configurações uniformes para todos os labels
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    
    # Atualizar configurações de fonte para ambos os gráficos
    for fig in [fig1, fig2]:
        fig.update_traces(
            textfont=dict(
                size=12,
                color='white'
            ),
            textangle=0
        )
        # Rotacionar labels do eixo x para melhor legibilidade
        fig.update_xaxes(tickangle=45)
    
    return fig1, fig2

def gerar_html_dashboard(df, fig1, fig2):
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
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Lançado", f"{int(df_filtrado['Nº Total de Unidades'].sum()):,}")
    with col2:
        st.metric("Total Vendido", f"{int(df_filtrado['Unidades Vendidas'].sum()):,}")
    with col3:
        st.metric("Total em Estoque", f"{int(df_filtrado['Qtd em Estoque'].sum()):,}")
    with col4:
        vso_total = (df_filtrado['Unidades Vendidas'].sum() / df_filtrado['Nº Total de Unidades'].sum() * 100)
        st.metric("VSO Médio", f"{vso_total:.1f}%")
    
    # Gráficos
    fig1, fig2 = criar_graficos_dashboard(df_filtrado)
    
    # Exibe os gráficos
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("Dados Detalhados")
    st.dataframe(df_filtrado)
    
    return fig1, fig2

if 'dashboard_data' not in st.session_state:
    st.warning("Por favor, selecione os dados na página principal primeiro.")
else:
    fig1, fig2 = mostrar_dashboard(st.session_state.dashboard_data)

    # Export options
    col2_1, col2_2, col2_3, col2_4 = st.columns([1, 1, 1, 1])
    
    # Excel export
    buffer_excel = BytesIO()
    st.session_state.dashboard_data.to_excel(buffer_excel, index=False)
    buffer_excel.seek(0)
    
    # HTML e PDF export
    html_content = gerar_html_dashboard(st.session_state.dashboard_data, fig1, fig2)
    
    
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