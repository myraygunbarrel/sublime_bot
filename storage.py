import redis
from config import REDIS_URL
from currency_parser import parse_currency
from location_analyzer import get_nearest
from collections import namedtuple


class DB:
    conn = None
    key = 'currency'
    cur_synonym = {
        ('евро', "eur", '€'): 'EUR',
        ('доллар', "бакс", "usd", 'dollar', '$'): 'USD'
    }

    def __init__(self):
        self.conn = redis.Redis(REDIS_URL)
        self.storage_tmp = dict()
        if not self.conn.exists(self.key):
            self._refresh_base()

    def get_currency(self):
        if not self.conn.exists(self.key):
            self._refresh_base()
        return self.conn.hgetall(self.key)

    def _refresh_base(self):
        currency_dict = parse_currency()
        self.conn.hmset(self.key, currency_dict)
        self.conn.expire(self.key, 3600)

    def add_place(self, user, place):
        self.storage_tmp[user] = [place]

    def add_location(self, user, location):
        self.storage_tmp[user].append(location)

    def add_photo(self, user, photo):
        self.storage_tmp[user].append(photo)

    def confirm_place(self, user):
        place_name = str(user) + '_' + self.storage_tmp[user][0]
        place_coord = str(self.storage_tmp[user][1].latitude) + ',' + \
                      str(self.storage_tmp[user][1].longitude)
        print(place_coord)
        place_photo = self.storage_tmp[user][2]
        set_name = str(user) + '_place_name'

        if not self.conn.sismember(set_name, place_name):
            self.conn.sadd(set_name, place_name)
            self.conn.rpush(user, place_name)
        else:
            self.conn.delete(place_name)

        self.conn.rpush(place_name, *[place_coord, place_photo])

        self.storage_tmp.pop(user, None)

    def cancel_place(self, user):
        self.storage_tmp.pop(user, None)

    def get_recent_places(self, user):
        Place = namedtuple('Place', ['name', 'location', 'photo'])
        places = self.conn.lrange(user, -3, -1)
        recent_places = list()
        for i, place_name in enumerate(places):
            place_data = self.conn.lrange(place_name, 0, -1)
            print(place_data)
            place_name = str(i+1) + ') ' + place_name.decode()[len(str(user))+1:] + ':'
            place_location = place_data[0].decode().split(',')
            place_photo = place_data[1].decode()
            recent_places.append(Place(place_name, place_location, place_photo))
        return recent_places

    def get_nearest_places(self, user, location):
        Place = namedtuple('Place', ['name', 'location', 'photo'])
        places = self.conn.lrange(user, 0, -1)

        place_locations = list()
        for place_name in places:
            place_location = self.conn.lindex(place_name, 0)
            place_locations.append(place_location.decode())

        print(place_locations)
        place_coord = str(location.latitude) + ',' + \
                      str(location.longitude)
        nearest_places_ind, distances = get_nearest(place_coord, '|'.join(place_locations))
        print(nearest_places_ind)
        nearest_places = list()
        for i, _ind in enumerate(nearest_places_ind):
            place_data = self.conn.lrange(places[_ind], 0, -1)
            print(place_data)
            place_name = str(i+1) + ') ' + places[_ind].decode()[len(str(user))+1:] + ' ({}):'.format(distances[i])
            print(place_data[0])
            place_location = place_data[0].decode().split(',')
            place_photo = place_data[1].decode()
            nearest_places.append(Place(place_name, place_location, place_photo))
        return nearest_places

    def erase_places(self, user):
        set_name = str(user) + '_place_name'
        self.conn.delete(set_name)
        self.conn.delete(user)


db = DB()
