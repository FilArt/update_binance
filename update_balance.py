import pytz
import gspread
from binance.client import Client
from datetime import datetime
from decimal import Decimal
from oauth2client.service_account import ServiceAccountCredentials
from requests import get
from secrets import API_KEY, API_SECRET, DOC_URL

timezone = pytz.timezone("Europe/Moscow")

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'path/to/creds/creds.json',
    scope,
)

gc = gspread.authorize(credentials)  # google client


def get_estimated_value(client):
    """
    Fetch estimated balance value.
    """
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
    """
    Convert bitcoin to xxx currency.
    """
    url = f"https://blockchain.info/tobtc?currency={xxx.upper()}&value=1"
    xxx_in_btc = 1 / Decimal(get(url).text) * btc
    return str(round(xxx_in_btc, 2))


def main():
    bc = Client(API_KEY, API_SECRET)  # binance client
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
