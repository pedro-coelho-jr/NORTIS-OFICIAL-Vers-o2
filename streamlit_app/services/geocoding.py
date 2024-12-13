import requests
from typing import Tuple, Optional

def get_coordinates(address: str, token: str, reference_point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """
    Obtém as coordenadas (latitude, longitude) de um endereço usando a API do Mapbox.
    
    Args:
        address: Endereço a ser geocodificado
        token: Token de acesso do Mapbox
        reference_point: Ponto de referência (longitude, latitude) para priorizar resultados próximos
        
    Returns:
        Tuple com (latitude, longitude) ou None se não encontrar
    """
    search_text = f"{address} São Paulo"
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{search_text}.json"
    
    params = {
        'access_token': token,
        'proximity': f"{reference_point[0]},{reference_point[1]}"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("features"):
            return None
            
        coordinates = data["features"][0]["geometry"]["coordinates"]
        # Mapbox retorna (longitude, latitude), mas vamos inverter para (latitude, longitude)
        return (coordinates[1], coordinates[0])
        
    except requests.exceptions.RequestException:
        return None 