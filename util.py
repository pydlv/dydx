import json

import dydx.constants as consts
import requests

from const import MINIMUM_EXPECTED_PROFIT_PER_TRADE_USDC, MINIMUM_EXPECTED_PROFIT_PER_TRADE_DAI
from enums import TradeDirection


def wei_to_token(wei: int, market: int) -> float:
    if market == 0:
        decimals = consts.DECIMALS_WETH
    elif market == 1:
        decimals = consts.DECIMALS_SAI
    elif market == 2:
        decimals = consts.DECIMALS_USDC
    elif market == 3:
        decimals = consts.DECIMALS_DAI
    else:
        raise ValueError('Invalid market number')

    return wei / (10 ** decimals)


def is_trade_profitable(
        price: float,
        amount: int,
        direction: TradeDirection,
        minimum: float,
        maximum: float) -> bool:
    """
    Step 1: 
    If buying:
    If price > minimum, return false
    If selling:
    If price < maximum, return false
    
    Step 2: Calculate the position we will have.
    
    Step 3:
    If the position is in DAI, assume we will be selling at maximum.
    If the position is in USDC, assume we will be buying at minimum.
    Calculate the final balance accordingly.
    
    Step 4:
    If final balance > original amount, and the difference meets the minimum profit, then it is a good trade.
    """

    # Step 1
    if direction == TradeDirection.Buy and price > minimum:
        return False
    elif direction == TradeDirection.Sell and price < maximum:
        return False

    # Step 2
    if direction == TradeDirection.Buy:
        position_market = consts.MARKET_DAI
        position_amount = amount * price
    else:
        position_market = consts.MARKET_USDC
        position_amount = amount / price

    # Step 3
    if position_market == consts.MARKET_DAI:
        final_amount = position_amount / maximum
    else:
        final_amount = position_amount * minimum

    return final_amount > amount


def calc_min_profit(amount: int, market: int, treat_min_as_percent: bool=True) -> float:
    if not treat_min_as_percent:
        if market == consts.MARKET_DAI:
            return MINIMUM_EXPECTED_PROFIT_PER_TRADE_DAI
        else:
            return MINIMUM_EXPECTED_PROFIT_PER_TRADE_USDC
    else:
        if market == consts.MARKET_DAI:
            return MINIMUM_EXPECTED_PROFIT_PER_TRADE_DAI * amount
        else:
            return MINIMUM_EXPECTED_PROFIT_PER_TRADE_USDC * amount


def calculate_max_price_for_buy(
        amount_usdc: int,
        predicted_sell_price: float
) -> float:
    """
    Calculates the highest price we can buy at, given a predicted sell price, and still meet the
    minimum profit requirement.
    :param amount_usdc: Amount wei in USDC that we are buying with.
    :param predicted_sell_price: The price that we predict we will sell our position.
    :return:
    """

    return (amount_usdc * predicted_sell_price) / (calc_min_profit(amount_usdc, consts.MARKET_USDC) + amount_usdc)


def calculate_min_price_for_sell(
        amount_dai: int,
        predicted_buy_price: float
) -> float:
    """
    Calculates the lowest price we can sell at, given a predicted buy back price, and still meet the
    minimum profit requirement.
    :param amount_dai: Amount wei in USDC that we are buying with.
    :param predicted_buy_price: The price that we predict we will buy out of our position.
    :return:
    """

    return predicted_buy_price * (calc_min_profit(amount_dai, consts.MARKET_DAI) + amount_dai) / amount_dai


def calculate_expected_profit_from_buy(
        price: float,
        amount_usdc: int,
        predicted_sell_price: float
) -> float:
    return amount_usdc * predicted_sell_price / price - amount_usdc


def calculate_expected_profit_from_sell(
        price: float,
        amount_dai: int,
        predicted_buy_price: float
) -> float:
    return amount_dai * price / predicted_buy_price - amount_dai


def wei_price_to_token_price(price: float) -> float:
    return price * 1e12


def token_price_to_wei_price(price: float) -> float:
    return price * 1e-12


def post_webhook_message(msg: str) -> None:
    data = json.dumps({
        "content": msg
    })

    response = requests.post('https://discordapp.com/api/webhooks/675179555853565978'
                             '/O0ZIfkgvVVkMQ44b0ElJCAgD6HS76rmKT6oWjlY3GDds7ykH7Qercwu6BmwkK0O004vd',
                             headers={"Content-Type": "application/json"},
                             data=data)
