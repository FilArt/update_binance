import pytz
import gspread
from binance.client import Client
from datetime import datetime
from decimal import Decimal
from oauth2client.service_account import ServiceAccountCredentials
from requests import get

DOC_URL = "https://docs.google.com/spreadsheets/d/1MyuGBuaNBrvh4k7KBASrA9rupL4JQrOIM5-IIlo4Ico/edit#gid=0"

timezone = pytz.timezone("Europe/Moscow")

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    '/home/art/Projects/Python/binance/src/creds/creds.json',
    scope,
)

gc = gspread.authorize(credentials)

API_KEY = 'V0nHzQkJg2xtEn9ZgQqdqZWyMFkvrTvc3cQWa2Vzn9SPek00ta1zGrqqgIpONShh'
API_SECRET = 'qn9Y0pxWNm7QyCQt0hxEAaW12A02pnTPbwAStviGthtJWclw1oxaG6060PvILsYl'


def get_estimated_value(client):
    all_prices = {
        t['symbol']: Decimal(t['price'])
        for t in client.get_symbol_ticker()
    }
    asset_balances = {
        b['asset'] + "BTC": Decimal(b['free']) + Decimal(b['locked'])
        for b in client.get_account()['balances']
    }
    asset_prices = {
        asset: all_prices[asset] * price
        for asset, price in asset_balances.items()
        if price > 0 and asset in all_prices
    }
    return sum(list(asset_prices.values())) + asset_balances['BTCBTC']


def btc_to_xxx(btc: Decimal, xxx: str):
    url = f"https://blockchain.info/tobtc?currency={xxx.upper()}&value=1"
    xxx_in_btc = 1 / Decimal(get(url).text) * btc
    return str(round(xxx_in_btc, 2))


def main():
    bc = Client(API_KEY, API_SECRET)
    dt_now = datetime.now(pytz.timezone('Europe/Moscow'))
    btc = get_estimated_value(bc)
    row = (
        'Binance',
        dt_now.date().strftime("%d-%m-%Y"),
        dt_now.time().strftime("%H:%M:%S"),
        btc,
        '=(D2-D3)/D3',
        btc_to_xxx(btc, 'usd').replace('.', ','),
        '=(F2-F3)/F3',
        btc_to_xxx(btc, 'rub').replace('.', ','),
        '=(H2-H3)/H3',
    )

    sh = gc.open_by_url(DOC_URL)
    ws = sh.sheet1

    ws.insert_row(row, index=2, value_input_option='USER_ENTERED')


if __name__ == '__main__':
    main()