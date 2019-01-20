import requests
import os
from collections import namedtuple


class LocationAnalyzer:
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    GOOGLE_TOKEN = os.environ.get('GOOGLE_API')
    Place = namedtuple('Place', ['name', 'location', 'photo'])

    def __init__(self, db):
        self.conn = db

    def parse_distance_matrix(self, location, places, radius=5000):
        params = {
            'mode': 'walking',
            'origins': location,
            'destinations': places,
            'key': self.GOOGLE_TOKEN
        }

        try:
            response = requests.get(self.url, params=params)
        except requests.exceptions.RequestException as e:
            return e, None

        distance_matrix = response.json()
        nearest = list()
        distances = list()
        for place_number, element in enumerate(distance_matrix['rows'][0]['elements']):
            if element['distance']['value'] < radius:
                nearest.append(place_number)
                distances.append(element['distance']['text'])

        return nearest, distances

    def get_recent_places(self, user):
        places = self.conn.lrange(user, -3, -1)

        if not places:
            return 'Используйте команду /add, чтобы добавить место'

        recent_places = self.prepare_places(user, places)
        return recent_places

    def get_nearest_places(self, user, location):
        places = self.conn.lrange(user, 0, -1)

        if not places:
            return 'Используйте команду /add, чтобы добавить место'

        place_locations = [self.conn.lindex(place_name, 0).decode() for place_name in places]

        place_coord = str(location.latitude) + ',' + str(location.longitude)
        nearest_places_ind, distances = self.parse_distance_matrix(place_coord, '|'.join(place_locations))

        if isinstance(nearest_places_ind, str):
            return 'Сервер недоступен. Попробуйте позже'
        if not distances:
            return 'Ничего нет поблизости'

        places = [self.conn.lindex(user, _ind) for _ind in nearest_places_ind]
        nearest_places = self.prepare_places(user, places, distances_in_km=distances)
        return nearest_places

    def prepare_places(self, user, places, distances_in_km=None):
        prepared_places = list()
        for i, place_name in enumerate(places):
            place_data = [x.decode() for x in self.conn.lrange(place_name, 0, -1)]
            place_name = str(i+1) + ') ' + place_name.decode()[len(str(user))+1:]

            if distances_in_km:
                place_name += ' ({}):'.format(distances_in_km[i])

            place_location = place_data[0].split(',')
            place_photo = place_data[1]
            prepared_places.append(self.Place(place_name, place_location, place_photo))
        return prepared_places
