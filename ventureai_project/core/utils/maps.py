# core/utils/maps.py
import requests
import os
from django.conf import settings

def get_similar_businesses(latitude, longitude, business_type="restaurant", radius=5000):
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise ValueError("API ключ для Google Maps не найден")

    endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': f"{latitude},{longitude}",
        'radius': radius,
        'type': business_type,
        'key': api_key
    }
    response = requests.get(endpoint_url, params=params)
    results = response.json().get('results', [])
    return results
