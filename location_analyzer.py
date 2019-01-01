import requests
from config import GOOGLE_API


def get_nearest(location, places, radius=900):
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    print(location, places)
    params = {
        'origins': location,
        'destinations': places,
        'key': GOOGLE_API
    }
    r = requests.get(url, params=params).json()
    nearest = list()
    for place_number, element in enumerate(r['rows'][0]['elements']):
        print(element['distance']['value'])
        if element['distance']['value'] < radius:
            nearest.append(place_number)

    return nearest


#
# origins = '41.43206,-81.38992'
# destinations = '41.43209,-81.38990|41.43229,-81.38980|41.43100,-81.38990'
# get_nearest(origins, destinations)