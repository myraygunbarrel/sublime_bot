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

    @classmethod
    def get_currency(cls):
        if not cls.conn.exists(cls.key):
            cls._refresh_base()
        return cls.conn.hgetall(cls.key)

    def _refresh_base(self):
        currency_dict = parse_currency()
        self.conn.hmset(self.key, currency_dict)
        self.conn.expire(self.key, 3600)


db = DB()
