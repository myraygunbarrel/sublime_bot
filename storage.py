import redis
from config import REDIS_URL
from currency_parser import parse_currency


class DB:
    conn = None
    key = 'currency'
    cur_synonym = {
        ('евро', "eur", '€'): 'EUR',
        ('доллар', "бакс", "usd", 'dollar', '$'): 'USD'
    }

    def __init__(self):
        self.conn = redis.Redis(REDIS_URL)
        self._refresh_base()
        self.storage_tmp = dict()

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
        place_coord = str(self.storage_tmp[user][1].longitude) + ' ' + \
                      str(self.storage_tmp[user][1].latitude)
        place_photo = self.storage_tmp[user][2]
        set_name = str(user) + '_place_name'

        if not self.conn.sismember(set_name, place_name):
            self.conn.sadd(set_name, place_name)
            self.conn.rpush(user, place_name)
        else:
            self.conn.delete(place_name)

        print(type(place_coord), type(place_photo))
        self.conn.rpush(place_name, *[place_coord, place_photo])

        self.storage_tmp.pop(user, None)

    def cancel_place(self, user):
        self.storage_tmp.pop(user, None)


db = DB()
