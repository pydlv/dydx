from dydx.constants import MARKET_USDC, MARKET_DAI
from dydx.util import token_to_wei

# Constants
HISTORY_LENGTH = 60
RISK: int = 50  # out of HISTORY LENGTH, where HISTORY LENGTH is the least amount of risk
MINIMUM_EXPECTED_PROFIT_PER_TRADE: float = 0.0015
TRADE_EXPIRATION_SECS = 6 * 3600  # Six hours


# Validation

assert RISK <= HISTORY_LENGTH - 2

# MINIMUM_EXPECTED_PROFIT_PER_TRADE_USDC = token_to_wei(MINIMUM_EXPECTED_PROFIT_PER_TRADE, MARKET_USDC)
# MINIMUM_EXPECTED_PROFIT_PER_TRADE_DAI = token_to_wei(MINIMUM_EXPECTED_PROFIT_PER_TRADE, MARKET_DAI)
MINIMUM_EXPECTED_PROFIT_PER_TRADE_USDC = MINIMUM_EXPECTED_PROFIT_PER_TRADE
MINIMUM_EXPECTED_PROFIT_PER_TRADE_DAI = MINIMUM_EXPECTED_PROFIT_PER_TRADE