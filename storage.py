import redis
import os
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
        self.conn = redis.from_url(os.getenv('REDIS_URL'))
        self.Place = namedtuple('Place', ['name', 'location', 'photo'])
        if not self.conn.exists(self.key):
            self._refresh_rates_info()

    def get_currency(self):
        if not self.conn.exists(self.key):
            self._refresh_rates_info()
        return self.conn.hgetall(self.key)

    def _refresh_rates_info(self):
        currency_dict = parse_currency()
        self.conn.hmset(self.key, currency_dict)
        self.conn.expire(self.key, 3600)

    def add_item(self, user, item):
        user_tmp = str(user) + '_tmp'
        self.conn.rpush(user_tmp, item)

    def add_location(self, user, location):
        user_tmp = str(user) + '_tmp'
        place_coord = str(location.latitude) + ',' + str(location.longitude)
        self.conn.rpush(user_tmp, place_coord)

    def confirm_place(self, user, cancel=False):
        user_tmp = str(user) + '_tmp'

        if not cancel:
            place_tmp = [x.decode() for x in self.conn.lrange(user_tmp, 0, -1)]

            place_name = str(user) + '_' + place_tmp[0]
            place_coord = place_tmp[1]
            place_photo = place_tmp[2]

            set_name = str(user) + '_place_name'

            if not self.conn.sismember(set_name, place_name):
                self.conn.sadd(set_name, place_name)
                self.conn.rpush(user, place_name)
            else:
                self.conn.delete(place_name)

            self.conn.rpush(place_name, *[place_coord, place_photo])

        self.conn.delete(user_tmp)

    def get_recent_places(self, user):
        places = self.conn.lrange(user, -3, -1)
        recent_places = list()
        for i, place_name in enumerate(places):
            place_data = [x.decode() for x in self.conn.lrange(place_name, 0, -1)]
            place_name = str(i+1) + ') ' + place_name.decode()[len(str(user))+1:] + ':'
            place_location = place_data[0].split(',')
            place_photo = place_data[1]
            recent_places.append(self.Place(place_name, place_location, place_photo))
        return recent_places

    def get_nearest_places(self, user, location):
        places = self.conn.lrange(user, 0, -1)

        place_locations = [self.conn.lindex(place_name, 0).decode() for place_name in places]

        place_coord = str(location.latitude) + ',' + str(location.longitude)
        nearest_places_ind, distances = get_nearest(place_coord, '|'.join(place_locations))

        if not distances:
            return 'Ничего нет поблизости'

        nearest_places = list()
        for i, _ind in enumerate(nearest_places_ind):
            place_data = [x.decode() for x in self.conn.lrange(places[_ind], 0, -1)]
            place_name = str(i+1) + ') ' + places[_ind].decode()[len(str(user))+1:] + ' ({}):'.format(distances[i])
            place_location = place_data[0].split(',')
            place_photo = place_data[1]
            nearest_places.append(self.Place(place_name, place_location, place_photo))
        return nearest_places

    def erase_places(self, user):
        set_name = str(user) + '_place_name'
        self.conn.delete(set_name)
        self.conn.delete(user)

    def get_state(self, message):
        user_state = str(message.chat.id) + '_state'
        return int(self.conn.get(user_state))

    def update_state(self, message, state):
        user_state = str(message.chat.id) + '_state'
        self.conn.set(user_state, state)


db = DB()
