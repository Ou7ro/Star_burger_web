import requests
from django.conf import settings
from django.core.cache import cache
from .models import CachedLocation


def get_cached_coordinates(address):
    """
    Получает координаты из кэша или API
    """
    if not address:
        return None, None

    cache_key = f'geocode_{address}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    try:
        location = CachedLocation.objects.get(address=address)
        if not location.is_expired():
            cache.set(cache_key, (location.latitude, location.longitude), 3600)
            return location.latitude, location.longitude
    except CachedLocation.DoesNotExist:
        pass

    return fetch_and_cache_coordinates(address)


def fetch_and_cache_coordinates(address):
    """
    Запрашивает координаты у API и сохраняет в кэш
    """
    try:

        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": settings.YANDEX_API_KEY,
            "format": "json",
        }, timeout=5)
        response.raise_for_status()

        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
        if not found_places:
            return None, None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        lat = float(lat)
        lon = float(lon)

        CachedLocation.objects.update_or_create(
            address=address,
            defaults={'latitude': lat, 'longitude': lon}
        )

        cache_key = f'geocode_{address}'
        cache.set(cache_key, (lat, lon), 3600)

        return lat, lon

    except (requests.RequestException, KeyError, ValueError) as e:
        print(f'Geocoding error for {address}: {str(e)}')

        CachedLocation.objects.get_or_create(
            address=address,
            defaults={'latitude': None, 'longitude': None}
        )

        return None, None
