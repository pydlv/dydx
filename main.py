import time
from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil
from typing import List

import gspread
import pandas
from dydx.constants import MARKET_DAI, MARKET_USDC
from dydx.util import token_to_wei
from oauth2client.service_account import ServiceAccountCredentials

from client import client
from const import RISK, HISTORY_LENGTH, TRADE_EXPIRATION_SECS
from sess import s
from util import *

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('My Project 44895-c802dfa0516d.json', scope)
google_client = gspread.authorize(creds)


def run() -> None:
    while True:
        print("Looped")

        now = datetime.now()
        month_ago = now - timedelta(days=HISTORY_LENGTH)

        fills_not_confirmed = list(filter(
            lambda fill: fill["status"] != "CONFIRMED",
            client.get_my_fills(["DAI-USDC"])["fills"]
        ))

        # Make sure all our fills are confirmed, otherwise our balances are thrown off and bad things happen.
        if len(fills_not_confirmed) == 0:
            iso = month_ago.isoformat() + 'Z'

            response = s.get(f"https://api.dydx.exchange/v1/candles/DAI-USDC?fromISO={iso}&res=1day")

            df = pandas.read_json(response.text)

            candles = df.candles

            assert len(df.candles) >= HISTORY_LENGTH - 1

            original_highs: List[float] = sorted(list(map(lambda candle: float(candle["high"]), candles)), reverse=True)
            highs = [token_price_to_wei_price(high) for high in original_highs]

            original_maximum = highs[RISK]
            maximum = original_maximum

            original_lows: List[float] = sorted(list(map(lambda candle: float(candle["low"]), candles)))
            lows = [token_price_to_wei_price(low) for low in original_lows]

            original_minimum = lows[RISK]
            minimum = original_minimum

            spread = maximum - minimum  # The greater, the better
            midpoint = (minimum + maximum) / 2

            assert 0.94 < wei_price_to_token_price(midpoint) < 1.06

            if spread <= 0:
                maximum = max(midpoint + 1e-16, maximum)
                minimum = min(midpoint - 1e-16, minimum)
                spread = maximum - minimum

            # This is absolutely necessary because we need to ensure we are always selling for higher than we are buying.
            assert spread > 0

            """
            We want to sell our DAI at a price of AT LEAST maximum, higher if possible.
            We want to buy our DAI at a price of AT MOST minimum, lower if possible.
            """

            # balance_usdc = wei_to_token(my_balances[MARKET_USDC], MARKET_USDC)
            # balance_dai = wei_to_token(my_balances[MARKET_DAI], MARKET_DAI)

            my_open_orders = list(filter(
                lambda order: order["status"] == "OPEN",
                client.get_my_orders(['DAI-USDC'])["orders"]
            ))

            my_balances = client.get_my_balances()["balances"]
            balance_usdc = float(my_balances[str(MARKET_USDC)]["wei"])
            balance_dai = float(my_balances[str(MARKET_DAI)]["wei"])

            num_buy_orders = len(list(filter(lambda order: order["side"] == "BUY", my_open_orders)))
            num_sell_orders = len(list(filter(lambda order: order["side"] == "SELL", my_open_orders)))

            for order in my_open_orders:
                if order["market"] == "DAI-USDC":
                    if order["side"] == "BUY":
                        balance_usdc -= ceil(float(order["quoteAmount"]))
                    else:
                        balance_dai -= ceil(float(order["baseAmount"]))

            if balance_usdc >= token_to_wei(22, MARKET_USDC) and num_buy_orders == 0:
                max_buy_price = min(calculate_max_price_for_buy(balance_usdc, maximum), minimum)

                print("USDC -> DAI -> USDC")
                print("max buy price", wei_price_to_token_price(max_buy_price))
                print("a_i", wei_to_token(balance_usdc, MARKET_USDC))

                a_p = ceil(balance_usdc / max_buy_price)
                a_f = ceil(a_p * maximum)

                print("a_p", wei_to_token(a_p, MARKET_DAI))
                print("a_f", wei_to_token(a_f, MARKET_USDC))

                print("m_b", wei_to_token(a_f - balance_usdc, MARKET_USDC))

                msg = f"""
-------------------------------------------------------------------------------
BUYING
makerAmount={wei_to_token(balance_usdc, MARKET_USDC)} USDC
takerAmount={wei_to_token(a_p, MARKET_DAI)} DAI
price={wei_price_to_token_price(max_buy_price)}
predictedProfit={wei_to_token(a_f - balance_usdc, MARKET_USDC)} USDC

min={wei_price_to_token_price(original_minimum)}
max={wei_price_to_token_price(original_maximum)}
-------------------------------------------------------------------------------
"""
                print(msg)
                post_webhook_message(msg)

                client.place_order(
                    market=consts.PAIR_DAI_USDC,
                    side=consts.SIDE_BUY,
                    amount=Decimal(a_p),
                    price=round(Decimal(max_buy_price), 16),
                    expiration=int(time.time()) + TRADE_EXPIRATION_SECS
                )

            if balance_dai >= token_to_wei(22, MARKET_DAI) and num_sell_orders == 0:
                print("DAI -> USDC -> DAI")

                min_sell_price = max(calculate_min_price_for_sell(balance_dai, minimum), maximum)

                print("min sell price", wei_price_to_token_price(min_sell_price))
                print("a_i", wei_to_token(balance_dai, MARKET_DAI))
                a_p = ceil(balance_dai * min_sell_price)
                a_f = ceil(a_p / minimum)

                print("a_p", wei_to_token(a_p, MARKET_USDC))
                print("a_f", wei_to_token(a_f, MARKET_DAI))

                print("m_b", wei_to_token(a_f - balance_dai, MARKET_DAI))

                msg = f"""
-------------------------------------------------------------------------------
SELLING
makerAmount={wei_to_token(balance_dai, MARKET_DAI)} DAI
takerAmount={wei_to_token(a_p, MARKET_USDC)} USDC
price={wei_price_to_token_price(min_sell_price)}
predictedProfit={wei_to_token(a_f - balance_dai, MARKET_DAI)} DAI
min={wei_price_to_token_price(original_minimum)}
max={wei_price_to_token_price(original_maximum)}
-------------------------------------------------------------------------------
"""

                print(msg)
                post_webhook_message(msg)

                client.place_order(
                    market=consts.PAIR_DAI_USDC,
                    side=consts.SIDE_SELL,
                    amount=Decimal(balance_dai),
                    price=round(Decimal(min_sell_price), 16),
                    expiration=int(time.time()) + TRADE_EXPIRATION_SECS
                )

            for order in my_open_orders:
                created_at = datetime.fromisoformat(order["createdAt"][:-1])
                now = datetime.utcnow()
                time_elapsed = now - created_at
                if time_elapsed.days >= 1:
                    client.cancel_order(order["id"])

        time.sleep(60)


if __name__ == "__main__":
    run()
