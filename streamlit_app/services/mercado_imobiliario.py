import pandas as pd
import streamlit as st
import numpy as np
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio

FILE_PATH = encontrar_arquivo("mercado_imobiliario.csv")
COORDINATES_FILE_PATH = encontrar_arquivo("coordenadas_lookup.csv")

@st.cache_data
def get_data():
    return pd.read_csv(FILE_PATH, low_memory=False)

@st.cache_data
def get_coordinates():
    return pd.read_csv(COORDINATES_FILE_PATH, low_memory=False)

def get_RGI_close_to_coordinates(coordinates: tuple[float, float], radius: float):
    coordinates_df = get_coordinates()
    # Seleciona apenas as colunas necessárias
    coordinates_df = coordinates_df[["Latitude", "Longitude", "RGI"]]
    
    lat, lon = coordinates
    # Converte apenas uma vez para radianos
    lat2 = np.radians(lat)
    lat1 = np.radians(coordinates_df["Latitude"].values)
    delta_lon = np.radians(coordinates_df["Longitude"].values - lon)
    
    R = 6371000

    a = np.sin((lat1 - lat2)/2)**2 + \
        np.cos(lat2) * np.cos(lat1) * np.sin(delta_lon/2)**2
    distances = 2 * R * np.arcsin(np.sqrt(a))
    
    # Usa boolean indexing direto
    return coordinates_df.loc[distances <= radius, "RGI"].tolist()

def get_all_info_RGI(rgis: list[int]):
    table = get_data()
    return table[table["RGI"].isin(rgis)]