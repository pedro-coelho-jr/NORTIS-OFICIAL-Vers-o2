import os
def encontrar_diretorio(nome_diretorio):
    # Começa na pasta atual se nenhuma for especificada
    pasta_inicial = os.path.abspath(os.path.dirname(__file__))

    # Lista de pastas a verificar, começando pela inicial
    pastas_a_verificar = []

    # Subir até a raiz, adicionando cada pasta à lista
    while True:
        pastas_a_verificar.append(pasta_inicial)

        # Se já estivermos na raiz, interrompe o loop
        nova_pasta = os.path.dirname(pasta_inicial)
        if nova_pasta == pasta_inicial:  # Isso significa que já estamos na raiz
            break

        pasta_inicial = nova_pasta

    # Agora, desce recursivamente a partir da raiz
    for pasta in pastas_a_verificar:
        for raiz, subpastas, arquivos in os.walk(pasta):
            if nome_diretorio in subpastas:  # Verifica se o diretório está nas subpastas
                return os.path.join(raiz, nome_diretorio)

    return None  # Diretório não encontrado