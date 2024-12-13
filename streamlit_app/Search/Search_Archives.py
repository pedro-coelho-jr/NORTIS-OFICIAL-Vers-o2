import os
def encontrar_arquivo(nome_arquivo, pasta_inicial=None):
       if pasta_inicial is None:
        pasta_inicial = os.getcwd()
        for raiz, pastas, arquivos in os.walk(pasta_inicial):
            if nome_arquivo in arquivos:
                return os.path.join(raiz, nome_arquivo)
        return None