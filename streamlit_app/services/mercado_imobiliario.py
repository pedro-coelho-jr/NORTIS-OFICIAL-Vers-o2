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
    # Calcula a distância em metros usando a fórmula de Haversine
    lat, lon = coordinates
    lat1 = coordinates_df["Latitude"].values * np.pi / 180
    lat2 = lat * np.pi / 180
    delta_lat = lat1 - lat2
    delta_lon = (coordinates_df["Longitude"].values - lon) * np.pi / 180
    
    # Raio da Terra em metros
    R = 6371000
    
    # Fórmula de Haversine
    a = np.sin(delta_lat/2)**2 + np.cos(lat2) * np.cos(lat1) * np.sin(delta_lon/2)**2
    distances = 2 * R * np.arcsin(np.sqrt(a))
    
    # Filtra pontos dentro do raio
    nearby_coordinates = coordinates_df[distances <= radius].copy()
    return nearby_coordinates["RGI"].tolist()

def get_all_info_RGI(rgis: list[int]):
    table = get_data()
    return table[table["RGI"].isin(rgis)]