# Listas de distritos por regioes utilizada no filtro de regioes
DISTRITOS_CENTRO = ['BELA VISTA', 'BOM RETIRO', 'CAMBUCI', 'CONSOLACAO', 'LIBERDADE', 'REPUBLICA', 'SANTA CECILIA', 'SE']

DISTRITOS_LESTE = ['ARICANDUVA', 'CARAO', 'VILA FORMOSA', 'CIDADE TIRADENTES', 'ERMELINO MATARAZZO', 'PONTE RASA', 'GUAIANASES', 
         'LAJEADO', 'ITAIM PAULISTA', 'VILA CURUCA', 'CIDADE LIDER', 'ITAQUERA', 'JOSE BONIFACIO', 'PARQUE DO CARMO', 
         'AGUA RASA', 'BELEM', 'BRAS', 'MOOCA', 'PARI', 'TATUAPE', 'ARTUR ALVIM', 'CANGAIBA', 'PENHA', 'VILA MATILDE', 
         'IGUATEMI', 'SAO MATEUS', 'SAO RAFAEL', 'JARDIM HELENA', 'SAO MIGUEL', 'VILA JACUI', 'SAO LUCAS', 'SAPOPEMBA', 
         'VILA PRUDENTE', 'CACHOEIRINHA', 'CASA VERDE']

DISTRITOS_NORTE = ['LIMAO', 'BRASILANDIA', 'FREGUESIA DO O', 'JACANA', 'TREMEMBE', 'ANHANGUERA', 'PERUS', 'JARAGUA', 'PIRITUBA', 
         'SAO DOMINGOS', 'MANDAQUI', 'SANTANA', 'TUCURUVI', 'VILA GUILHERME', 'VILA MARIA', 'VILA MEDEIROS']

DISTRITOS_OESTE = ['BUTANTA', 'MORUMBI', 'RAPOSO TAVARES', 'RIO PEQUENO', 'VILA SONIA', 'BARRA FUNDA', 'JAGUARA', 'JAGUARE',
         'LAPA', 'PERDIZES', 'VILA LEOPOLDINA', 'ALTO DE PINHEIROS', 'ITAIM BIBI', 'JARDIM PAULISTA', 'PINHEIROS']

DISTRITOS_SUL = ['CAMPO LIMPO', 'CAPAO REDONDO', 'VILA ANDRADE', 'CIDADE DUTRA', 'GRAJAU', 'SOCORRO', 'CIDADE ADEMAR', 'PEDREIRA', 
       'CURSINO', 'IPIRANGA', 'SACOMA', 'JABAQUARA', 'JARDIM ANGELA', 'MBOI MIRIM', 'JARDIM SAO LUIS', 'MARSILAC', 
       'PARELHEIROS', 'CAMPO BELO', 'SANTO AMARO', 'CAMPO GRANDE', 'MOEMA', 'VILA MARIANA', 'SAUDE']

#Categoria dos estabelecimentos
CATEGORIAS = {
    "Comércio e Serviços": [
        "Fast Food", "Agencia Bancaria", "Academia de Ginastica", "Faculdade",
        "Hipermercados e Supermercados", "Restaurante", "Petshop", "Shopping Center",
        "Hortifruti",
    ],
    "Educação e Saúde": [
        "Escola Privada", "Escola Pública", "Hospital", "Farmacia",
    ],
    "Feira Livre": [
        "Feira Livre",
    ]
}

# Dicionários de cores
COLOR_MAP = {'lote': 'green', 'condominio': 'blue'}

COLOR_DICT_ESTABELECIMENTOS = {
    'Escola Privada': 'red',
    'Escola Pública': 'brown',
    'Fast Food': 'green',
    'Agencia Bancaria': 'purple',
    'Academia de Ginastica': 'yellow',
    'Faculdade': 'darkgreen',
    'Hipermercados e Supermercados': 'teal',
    'Hospital': 'cyan',
    'Petshop': 'deepskyblue',
    'Restaurante': 'orange',
    'Shopping Center': 'magenta',
    'Feira Livre': 'blue',
    "Farmacia": "olive",
    "Hortifruti": "gray",
}

COLOR_DICT_MOBILITY = {
    'Estacao de Metro': 'darkred',
    'Projetos de Estacao de Metro': 'royalblue',
    'Estacao de Trem': 'forestgreen',
    'Projetos de Estacao de Trem': 'black',
    'Ponto de onibus': 'goldenrod',
    'Terminal de onibus': 'darkorange',
    'Corredor Onibus': 'darkblue',
    'Ferrovia mdc': 'indigo',
    'Linha metro projeto': 'darkviolet',
    'Linha metro': 'deeppink',
    'Linha trem projeto': 'slategray',
    'Linha trem': 'limegreen',
}

# Dicionários de cores para as linhas de metrô e projeto de metro
LINE_COLORS = {
    'AZUL': 'blue',
    'VERDE': 'green',
    'VERMELHA': 'red',
    'LILAS': 'purple',
    'PRATA': 'silver',
    'AMARELA': 'yellow',
    'VIOLETA': 'violet',
    'CELESTE': 'skyblue',
    'ROSA': 'pink',
    'MARROM': 'brown',
    'OURO': 'gold',
    'LARANJA': 'orange',
}

# Lista de mobilidades que serão plotadas como linha
LINE_MOBILITIES = [
    'Ferrovia mdc',
    'Linha metro projeto',
    'Linha metro',
    'Linha trem projeto',
    'Linha trem',
]
