from bs4 import BeautifulSoup
import datetime
import requests


class CurrencyHandler:
    key = 'currency'
    cur_synonym = {
        ('евро', "eur", '€'): 'EUR',
        ('доллар', "бакс", "usd", 'dollar', '$'): 'USD'
    }

    def __init__(self, db):
        self.conn = db
        if not self.conn.exists(self.key):
            self._refresh_rates_info()

    @staticmethod
    def parse_currency():
        date = datetime.date.today().strftime("%d/%m/%Y")
        try:
            result = requests.get("http://www.cbr.ru/scripts/XML_daily.asp", {"date_req": date})
        except requests.exceptions.RequestException as e:
            return
        soup = BeautifulSoup(result.content, 'xml')
        list_of_currencies = {}
        for c in soup('Valute'):
            list_of_currencies[c.CharCode.string] = c.Value.string
        return list_of_currencies

    def get_currency(self):
        if not self.conn.exists(self.key):
            self._refresh_rates_info()
        return self.conn.hgetall(self.key)

    def _refresh_rates_info(self):
        currency_dict = self.parse_currency()
        if currency_dict:
            self.conn.hmset(self.key, currency_dict)
            self.conn.expire(self.key, 3600)

    def currency_interpreter(self, message):
        for key in self.cur_synonym:
            for syn in key:
                if syn in message:
                    proper_key = self.cur_synonym[key]
                    return proper_key, self.get_currency()[proper_key.encode()].decode()
        return None, None
