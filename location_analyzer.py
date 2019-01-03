import requests
import os
from config import GOOGLE_API


def get_nearest(location, places, radius=5000):
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    params = {
        'mode': 'walking',
        'origins': location,
        'destinations': places,
        'key': os.environ(os.environ.get('GOOGLE_API'), GOOGLE_API)
    }
    response = requests.get(url, params=params).json()
    nearest = list()
    distances = list()
    for place_number, element in enumerate(response['rows'][0]['elements']):
        if element['distance']['value'] < radius:
            nearest.append(place_number)
            distances.append(element['distance']['text'])

    return nearest, distances
