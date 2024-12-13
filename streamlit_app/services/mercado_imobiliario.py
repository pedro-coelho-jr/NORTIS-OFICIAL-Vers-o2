import pandas as pd
import streamlit as st
import numpy as np
from memory_profiler import profile
from Search.Search_Archives import encontrar_arquivo
from Search.Search_Diretory import encontrar_diretorio
import gc

FILE_PATH = encontrar_arquivo("mercado_imobiliario.csv")
COORDINATES_FILE_PATH = encontrar_arquivo("coordenadas_lookup.csv")

@profile
@st.cache_data
def get_data():
    return pd.read_csv(FILE_PATH, low_memory=False)

@profile
@st.cache_data
def get_coordinates():
    return pd.read_csv(COORDINATES_FILE_PATH, low_memory=False)

@profile
def get_RGI_close_to_coordinates(coordinates: tuple[float, float], radius: float):
    coordinates_df = get_coordinates()
    # Liberar memória após uso
    coordinates_df = coordinates_df[["Latitude", "Longitude", "RGI"]].copy()
    
    lat, lon = coordinates
    lat2 = np.radians(lat)
    lat1 = np.radians(coordinates_df["Latitude"].values)
    delta_lon = np.radians(coordinates_df["Longitude"].values - lon)
    
    R = 6371000

    a = np.sin((lat1 - lat2)/2)**2 + \
        np.cos(lat2) * np.cos(lat1) * np.sin(delta_lon/2)**2
    distances = 2 * R * np.arcsin(np.sqrt(a))
    
    result = coordinates_df.loc[distances <= radius, "RGI"].tolist()
    
    # Limpar referências
    del coordinates_df, lat1, delta_lon, distances
    return result

@profile
def get_all_info_RGI(rgis: list[int]):
    table = get_data()
    return table[table["RGI"].isin(rgis)].copy()