import pandas as pd
import streamlit as st

def criar_card(
    empreendimento,
    endereco,
    incorporadora,
    lancamento,
    preco_m2,
    ticket,
    area,
    vagas,
    dorms,
    estoque_total,
    infraestrutura,
    unidades_disponiveis,
    total_lancado,
    total_vendido,
    total_estoque,
    vso
):
    """
    Cria um card estilizado no Streamlit com as informações do empreendimento.

    Args:
        empreendimento (str): Nome do empreendimento.
        endereco (str): Endereço do empreendimento.
        incorporadora (str): Nome da incorporadora.
        lancamento (str): Data de lançamento.
        tipologia (str): Tipo do imóvel (ex.: Comercial, Residencial).
        preco_m2 (str): Faixa de preço por metro quadrado.
        ticket (str): Faixa de valor do ticket.
        area (str): Faixa de área útil.
        vagas (str): Número de vagas disponíveis.
        dorms (str): Número de dormitórios.
        estoque_total (int): Quantidade total em estoque.
        infraestrutura (str): Detalhes de infraestrutura.
    """
    st.markdown(
        f"""
            <div style="border: 1px solid #ccc; border-radius: 8px; padding: 10px; margin-bottom: 5px; background-color: #f9f9f9; font-family: Arial, sans-serif; font-size: 0.9em;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #333; font-size: 1.1em; margin-bottom: 0px;"><span title="Empreendimento">🏢</span> {empreendimento} - {incorporadora}</h3>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 1em;">
                    <p style="margin: 0; color: #555; font-size: 0.85em;"><span title="Endereço">📍</span> {endereco}</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Data de Lançamento">📅</span> {lancamento}</p>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 1em; margin-top: 5px;">
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Preço por m²">💵</span> {preco_m2}</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Total Lançado">📈</span> Total Lançado: {total_lancado}</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Total Vendido">📉</span> Total Vendido: {total_vendido}</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Total Estoque">📦</span> Total Estoque: {total_estoque}</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="VSO">📊</span> VSO: {vso:.0f}%</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Área">📐</span> Área: {area}</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Vagas de Garagem">🚗</span> Vagas: {vagas}</p>
                    <p style="margin: 0; color: #555; font-size: 1em;"><span title="Dormitórios">🛏️</span> Dorms: {dorms}</p>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

def processar_dataframe(df):
    """
    Processa o dataframe e calcula valores agregados para criar um card único.
    """
    # Valores first
    empreendimento = df['Empreendimento'].iloc[0]
    endereco = df['Endereço'].iloc[0]
    incorporadora = df['Grupo Incorporador Apelido'].iloc[0]
    lancamento = df['Data Lançamento'].iloc[0]
    # remove anything after the first space
    lancamento = lancamento.split(" ")[0]

    # Calcular a soma do total de estoque
    estoque_total = df['Qtd em Estoque'].sum()

    # Calcular ranges
    area_min = df['Área Total'].min()
    area_max = df['Área Total'].max()
    area_range = f"{area_min} - {area_max} m²"

    vagas_min = df['Nº Vagas'].min()
    vagas_max = df['Nº Vagas'].max()
    vagas_range = f"{vagas_min} - {vagas_max}"

    dorms_min = int(df['Dormitórios'].min())
    dorms_max = int(df['Dormitórios'].max())
    dorms_range = f"{dorms_min} - {dorms_max}"

    # Calcular o range de preço por m²
    preco_m2_min = df['(VUV)Preço m2 privativo atualizado CUB'].min()
    preco_m2_max = df['(VUV)Preço m2 privativo atualizado CUB'].max()
    preco_m2_range = f"R$ {preco_m2_min:,.2f} - R$ {preco_m2_max:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Calcular o range de ticket
    ticket_min = df['(VMU)Preço de venda da unidade atualizado CUB'].min()
    ticket_max = df['(VMU)Preço de venda da unidade atualizado CUB'].max()
    ticket_range = f"R$ {ticket_min:,.2f} - R$ {ticket_max:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Selecionar a infraestrutura mais completa (a mais longa)
    infraestrutura = df.loc[df['Infraestrutura'].str.len().fillna(0).idxmax(), 'Infraestrutura'] if not df['Infraestrutura'].isna().all() else ""

    # Lista de unidades únicas
    unidades = ", ".join(df['Unidade'].unique())

    # Calcular total lançado, total vendido e total estoque
    total_lancado = df['Nº Total de Unidades'].sum()
    total_vendido = df['Unidades Vendidas'].sum()
    total_estoque = df['Qtd em Estoque'].sum()

    # Calcular VSO
    vso = (total_vendido / total_lancado) * 100 if total_lancado > 0 else 0

    # Calcular vagas totais (multiplicando pelo número total de unidades)
    vagas_total = int((df['Nº Vagas'] * df['Nº Total de Unidades']).sum())
    
    # Calcular dormitórios (sem range)
    dorms_total = int(df['Dormitórios'].sum())

    # Arredondar valores para inteiros
    total_lancado = int(df['Nº Total de Unidades'].sum())
    total_vendido = int(df['Unidades Vendidas'].sum())
    total_estoque = int(df['Qtd em Estoque'].sum())
    estoque_total = int(df['Qtd em Estoque'].sum())

    # Chamar a função criar_card com os valores agregados
    criar_card(
        empreendimento=empreendimento,
        endereco=endereco,
        incorporadora=incorporadora,
        lancamento=lancamento,
        preco_m2=preco_m2_range,
        ticket=ticket_range,
        area=area_range,
        vagas=vagas_total,
        dorms=dorms_range,
        estoque_total=estoque_total,
        infraestrutura=f"{infraestrutura}",
        unidades_disponiveis=unidades,
        total_lancado=total_lancado,
        total_vendido=total_vendido,
        total_estoque=total_estoque,
        vso=vso
    )