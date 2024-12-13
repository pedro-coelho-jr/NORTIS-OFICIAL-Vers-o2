import pandas as pd
import streamlit as st

# Dicionário de pesos
pesos = {
    "Estacao de Metro": 10,
    "Estacao de Trem": 7,
    "Monotrilho": 7,
    "Terminal de onibus": 3,
    "Ponto de onibus": 3,
    "Shopping Center": 10,
    "Hipermercados e Supermercados": 10,
    "Farmacia": 5,
    "Padarias": 5,
    "Escola Privada": 5,
    "Escola Pública": 5,
    "Faculdade": 5,
    "Hospital": 4,
    "Postos de saúde": 4,
    "Academia de Ginastica": 6,
    "Hortifruti": 6,
    "Agencia Bancaria": 5,
}

# Categorias e Itens esperados

itens_mobilidade = ["Estacao de Metro", "Estacao de Trem", "Monotrilho", "Terminal de onibus", "Ponto de onibus"]

itens_comercio_servicos = ["Shopping Center", "Hipermercados e Supermercados", "Farmacia", "Padarias"]

itens_educacao_saude = ["Escola Privada", "Escola Pública", "Faculdade", "Hospital", "Postos de saúde"]

itens_comercio_servicos_secundarios = ["Academia de Ginastica", "Hortifruti", "Agencia Bancaria"]

# Funções para calcular status e escala
def calcular_status(distancia):
    if distancia <= 300:
        return "Excelente"
    elif distancia <= 500:
        return "Satisfatório"
    elif distancia <= 1000:
        return "Regular"
    elif distancia <= 1500:
        return "Insatisfatório"
    else:
        return "Muito Insatisfatório"

def calcular_escala(distancia):
    if distancia <= 300:
        return 10
    elif distancia <= 500:
        return 8
    elif distancia <= 1000:
        return 6
    elif distancia <= 1500:
        return 4
    else:
        return 2

# Função para gerar a pontuacao

def pontuacao(ponto, categoria, item):
    if ponto.empty:
            distancia = "-"
            status = "-"
            escala = 0
            total = 0
    else:
        distancia = ponto["Distancia (m)"].values[0]
        status = calcular_status(distancia)
        escala = calcular_escala(distancia)
        peso = pesos.get(item, 0)
        total = (peso / 100) * escala

    dict = {
        "Categoria": categoria,
        "Item": item,
        "Peso (%)": pesos.get(item, 0),
        "Distância (m)": distancia,
        "Status": status,
        "Escala": escala,
        "Total": total
    }
    # Adicionar a linha à tabela
    return dict

# Função para gerar a tabela
def gerar_pontuacao(mob_mais_proximos, estab_mais_proximos):
    # Inicializar a lista para armazenar as linhas da tabela final
    tabela_final = []

    # Criar a tabela com todas as categorias e itens, incluindo pontos não encontrados
    for categoria in ["Mobilidade", "Comércio e Serviços", "Educação e Saúde", "Comércio e Serviços Secundários"]:
        if categoria == "Mobilidade":
            for item in itens_mobilidade:
                ponto_encontrado = mob_mais_proximos[mob_mais_proximos["Tipo"] == item]
                tabela_final.append(pontuacao(ponto = ponto_encontrado, categoria = categoria, item = item))
        elif categoria == "Comércio e Serviços":
            for item in itens_comercio_servicos:
                ponto_encontrado = estab_mais_proximos[estab_mais_proximos["Tipo"] == item]
                tabela_final.append(pontuacao(ponto = ponto_encontrado, categoria = categoria, item = item))
        elif categoria == "Educação e Saúde":
            for item in itens_educacao_saude:
                ponto_encontrado = estab_mais_proximos[estab_mais_proximos["Tipo"].isin(["Escola Privada", "Escola Pública", "Faculdade", "Hospital", "Postos de saúde"])]
                tabela_final.append(pontuacao(ponto = ponto_encontrado, categoria = categoria, item = item))
        elif categoria == "Comércio e Serviços Secundários":
            for item in itens_comercio_servicos_secundarios:
                ponto_encontrado = estab_mais_proximos[estab_mais_proximos["Tipo"].isin(["Academia de Ginastica", "Hortifruti", "Agencia Bancaria"])]
                tabela_final.append(pontuacao(ponto = ponto_encontrado, categoria = categoria, item = item))
        else:
            ponto_encontrado = pd.DataFrame()  # Não há dados para essas categorias

    # Criar DataFrame com os dados finais
    df_final = pd.DataFrame(tabela_final)

    # Adicionar a última linha com o score
    score = df_final["Total"].sum()
    df_final.loc[len(df_final)] = ["Score", "", "", "", "", "", score]

    # Exibir a tabela no Streamlit
    return df_final, score
    #st.dataframe(df_final.set_index("Categoria"))

def exibir_score(score):
    st.markdown(
        """
        <style>
        .metric-container {
            display: flex;
            justify-content: center; /* Centraliza horizontalmente */
            align-items: center;    /* Centraliza verticalmente */
            margin-top: 0px;       /* Margem superior */
            margin-bottom: 40px;
        }
        .custom-metric {
            background-color: #1f77b4; /* Cor de fundo */
            color: white;             /* Cor do texto */
            border-radius: 10px;      /* Bordas arredondadas */
            padding: 30px 80px;       /* Espaçamento interno */
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2); /* Sombra */
            font-size: 24px;          /* Tamanho da fonte */
            text-align: center;       /* Centralização do texto */
        }
        </style>
        """,
        unsafe_allow_html=True)
    st.markdown(
            f"""
            <div class="metric-container">
                <div class="custom-metric">
                    <strong>Pontuação</strong><br>
                    {score}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )