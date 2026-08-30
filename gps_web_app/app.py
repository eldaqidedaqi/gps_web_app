#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GPS Web App with Flask
Aplicación para buscar ubicaciones, calcular distancias y triangular posiciones GPS
"""

import os
import math
from flask import Flask, render_template, request, jsonify, redirect, url_for
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import logging
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

# Crear aplicación Flask
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuración
app.config['DEBUG'] = True
app.config['TESTING'] = False
app.config['ENV'] = 'development'

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar geocodificador (Nominatim - OpenStreetMap)
# user_agent es requerido por Nominatim
geolocator = Nominatim(user_agent="gps_web_app_2026")

# Constantes
EARTH_RADIUS_KM = 6371.0  # Radio de la Tierra en kilómetros
DEFAULT_TIMEOUT = 10  # Timeout para geocodificación

logger.info("✅ GPS Web App inicializada correctamente")

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos usando la fórmula Haversine.
    
    Args:
        lat1, lon1: Latitud y longitud del punto 1 (en grados)
        lat2, lon2: Latitud y longitud del punto 2 (en grados)
    
    Returns:
        Distancia en kilómetros (float)
    """
    # Convertir a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula Haversine
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = EARTH_RADIUS_KM * c
    return distance


def geocode_location(location_name):
    """
    Convierte un nombre de ubicación a coordenadas GPS (lat, lon).
    
    Args:
        location_name: Nombre de la ciudad o dirección
    
    Returns:
        Tupla (lat, lon, location_name) o (None, None, None) si no se encuentra
    """
    try:
        location = geolocator.geocode(location_name, timeout=DEFAULT_TIMEOUT)
        if location:
            logger.info(f"✅ Ubicación encontrada: {location_name} -> ({location.latitude}, {location.longitude})")
            return location.latitude, location.longitude, location.address
        else:
            logger.warning(f"⚠️ Ubicación no encontrada: {location_name}")
            return None, None, None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.error(f"❌ Error al geocodificar {location_name}: {str(e)}")
        return None, None, None
    except Exception as e:
        logger.error(f"❌ Error inesperado al geocodificar: {str(e)}")
        return None, None, None


def trilateration(lat1, lon1, d1, lat2, lon2, d2, lat3, lon3, d3):
    """
    Calcula la posición de un punto desconocido usando triangulación (trilateration).
    Utiliza tres puntos de referencia y sus distancias al punto desconocido.
    
    Args:
        lat1, lon1: Coordenadas del punto 1
        d1: Distancia desde punto 1 al punto desconocido (km)
        lat2, lon2: Coordenadas del punto 2
        d2: Distancia desde punto 2 al punto desconocido (km)
        lat3, lon3: Coordenadas del punto 3
        d3: Distancia desde punto 3 al punto desconocido (km)
    
    Returns:
        Tupla (lat_calculada, lon_calculada) o (None, None) si no se puede calcular
    """
    try:
        # Convertir distancias de km a grados (aproximado)
        # 1 grado de latitud ≈ 111 km
        # 1 grado de longitud ≈ 111 * cos(latitud) km
        
        d1_deg = d1 / 111.0
        d2_deg = d2 / 111.0
        d3_deg = d3 / 111.0
        
        # Usar método iterativo simple (centroide ponderado)
        # Ponderación inversamente proporcional a la distancia
        if d1 == 0 or d2 == 0 or d3 == 0:
            return None, None
        
        weight1 = 1.0 / (d1 + 0.1)  # Evitar división por cero
        weight2 = 1.0 / (d2 + 0.1)
        weight3 = 1.0 / (d3 + 0.1)
        
        total_weight = weight1 + weight2 + weight3
        
        calc_lat = (lat1 * weight1 + lat2 * weight2 + lat3 * weight3) / total_weight
        calc_lon = (lon1 * weight1 + lon2 * weight2 + lon3 * weight3) / total_weight
        
        logger.info(f"✅ Triangulación calculada: ({calc_lat}, {calc_lon})")
        return calc_lat, calc_lon
    
    except Exception as e:
        logger.error(f"❌ Error en triangulación: {str(e)}")
        return None, None


def validate_coordinates(lat, lon):
    """
    Valida que las coordenadas estén dentro de rangos válidos.
    
    Args:
        lat: Latitud (-90 a 90)
        lon: Longitud (-180 a 180)
    
    Returns:
        True si son válidas, False en caso contrario
    """
    try:
        lat = float(lat)
        lon = float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def format_distance_conversions(distance_km):
    """
    Convierte una distancia en km a varias unidades.
    
    Args:
        distance_km: Distancia en kilómetros
    
    Returns:
        Diccionario con conversiones
    """
    return {
        'km': round(distance_km, 2),
        'meters': round(distance_km * 1000, 0),
        'miles': round(distance_km * 0.621371, 2),
        'nautical_miles': round(distance_km * 0.539957, 2),
        'yards': round(distance_km * 1093.613, 0)
    }
