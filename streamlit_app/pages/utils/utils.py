import geopandas as gpd
import pandas as pd
from pathlib import Path
from .constants import CATEGORIAS
import os

def load_geojson(directory_path):
    gdf = gpd.read_file(directory_path)
    return gdf

def gdf_to_df(gdf):
    gdf = gdf.drop(columns = ['geometry'])
    return gdf

def convert_to_int(x):
    try:
        return int(float(x))
    except (ValueError, TypeError):
        return x
    
# Função para carregar e preparar dados das planilhas
def load_and_prepare_excel_data(file_path):
    df = pd.read_excel(file_path)
    # Verifica se as colunas de coordenadas estão presentes
    if 'longitude' in df.columns and 'latitude' in df.columns:
        # Normaliza as colunas para manter o padrão
        df.rename(columns={'longitude': 'Longitude', 'latitude': 'Latitude'}, inplace=True)
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        
        # Verifica se há dados vazios de longitude e latitude e os remove
        df = df.dropna(subset=['Longitude', 'Latitude'])
    return df

def load_all_xlsx_in_directory(folder_path):
    folder = Path(folder_path)
    return {file.stem: load_and_prepare_excel_data(file) for file in folder.glob("*.xlsx")}


# Função para categorizar os estabelecimentos
def categorizar_estabelecimento(tipo):
    for categoria, tipos in CATEGORIAS.items():
        if tipo in tipos:
            return categoria
    return "Outros"


def load_mobility_data(xlsx_directory, geojson_directory, geojson_files):
    # Carrega os dados XLSX
    mobility_data = load_all_xlsx_in_directory(xlsx_directory)
    # Carrega os dados GeoJSON e adiciona ao dicionário
    for geojson_file in geojson_files:
        file_path = os.path.join(geojson_directory, geojson_file)
        if os.path.exists(file_path):
            gdf = gpd.read_file(file_path)
            key = geojson_file.replace('.geojson', '')  # Remove a extensão para formar a chave
            mobility_data[key] = gdf
        else:
            print(f"Arquivo {geojson_file} não encontrado no diretório {geojson_directory}.")

    return mobility_data

