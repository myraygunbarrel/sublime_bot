from bs4 import BeautifulSoup
import datetime
import requests


def parse_currency():
    date = datetime.date.today().strftime("%d/%m/%Y")
    result = requests.get("http://www.cbr.ru/scripts/XML_daily.asp", {"date_req": date})
    soup = BeautifulSoup(result.content, 'xml')
    list_of_currencies = {}
    for c in soup('Valute'):
        list_of_currencies[c.CharCode.string] = c.Value.string
    return list_of_currencies

