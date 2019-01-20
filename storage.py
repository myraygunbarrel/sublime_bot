import redis
import os


class DB:
    conn = None

    def __init__(self):
        self.conn = redis.from_url(os.getenv('REDIS_URL', 'localhost'))

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
            self.save_place(user, user_tmp)
        self.conn.delete(user_tmp)

    def save_place(self, user, user_tmp):
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

    def erase_places(self, user):
        set_name = str(user) + '_place_name'
        self.conn.delete(set_name)
        self.conn.delete(user)

    def get_state(self, message):
        user_state = str(message.chat.id) + '_state'
        if self.conn.exists(user_state):
            state = int(self.conn.get(user_state))
        else:
            state = 0
            self.update_state(message, state)
        return state

    def update_state(self, message, state):
        user_state = str(message.chat.id) + '_state'
        self.conn.set(user_state, state)


db = DB()
