import requests
from decimal import Decimal, ROUND_HALF_UP

# CoinGecko API URL for Tether (USDT) price in Iranian Rial (IRR)
# Note: CoinGecko might not directly support IRR with high liquidity or frequency.
# We'll use USD as an intermediary if direct IRR is problematic, then apply a known USD to IRR rate.
# For now, let's assume a direct or an acceptable proxy is available.
# The API endpoint for simple price: /simple/price
# ids=tether, vs_currencies=irr
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# It's good practice to use a session for requests
http_session = requests.Session()
http_session.headers.update({"Accept": "application/json"})

def get_usdt_to_irr_price() -> Decimal | None:
    """
    Fetches the current price of 1 USDT in IRR from CoinGecko.

    Returns:
        Decimal: The price of 1 USDT in IRR, or None if fetching fails.
    """
    params = {
        "ids": "tether",
        "vs_currencies": "irr"
    }
    try:
        response = http_session.get(COINGECKO_URL, params=params, timeout=10) # 10 seconds timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()

        # Expected response structure: {'tether': {'irr': 12345.67}}
        price = data.get("tether", {}).get("irr")

        if price is not None:
            return Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) # Quantize to 2 decimal places for IRR
        else:
            print("Could not find 'irr' price for 'tether' in CoinGecko response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching USDT price from CoinGecko: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Error parsing CoinGecko response: {e}")
        return None

def get_usdt_to_usd_price() -> Decimal | None:
    """
    Fetches the current price of 1 USDT in USD from CoinGecko.
    This can be a fallback or primary source if direct IRR is unstable.
    """
    params = {
        "ids": "tether",
        "vs_currencies": "usd"
    }
    try:
        response = http_session.get(COINGECKO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get("tether", {}).get("usd")
        if price is not None:
            # USDT is pegged to USD, so price should be very close to 1.
            # We still use Decimal for consistency.
            return Decimal(str(price)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        else:
            print("Could not find 'usd' price for 'tether' in CoinGecko response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching USDT->USD price from CoinGecko: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Error parsing CoinGecko USDT->USD response: {e}")
        return None

# TODO: The bot owner might need to set the USD to IRR exchange rate manually if CoinGecko IRR is not reliable.
# This could be stored in config.py or an admin command.
MANUAL_USD_TO_IRR_RATE = Decimal("500000") # Example: 500,000 IRR per 1 USD. Replace with actual or make configurable.

def get_usdt_price_in_irr_preferred() -> tuple[Decimal | None, str]:
    """
    Tries to get USDT to IRR price. Uses direct CoinGecko IRR if available,
    otherwise falls back to USDT->USD and a manual USD->IRR rate.

    Returns:
        tuple[Decimal | None, str]: (Price in IRR, source_description string)
                                     None if price cannot be determined.
    """
    price_irr = get_usdt_to_irr_price()
    if price_irr:
        return price_irr, "direct from CoinGecko (USDT/IRR)"

    # Fallback to USDT/USD and manual rate
    # print("Direct USDT/IRR from CoinGecko failed or not available. Trying USDT/USD and manual rate.")
    # price_usd = get_usdt_to_usd_price()
    # if price_usd:
    #     # Assuming USDT is very close to 1 USD, this price_usd is effectively the peg accuracy.
    #     # The final price would be price_usd * MANUAL_USD_TO_IRR_RATE
    #     # However, for simplicity, we can assume 1 USDT = 1 USD for this conversion
    #     final_irr_price = Decimal("1.0") * MANUAL_USD_TO_IRR_RATE
    #     return final_irr_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), f"manual rate (1 USDT ~ 1 USD @ {MANUAL_USD_TO_IRR_RATE} IRR/USD)"

    # For MVP, let's rely on a manually set rate if CoinGecko IRR is not available.
    # This avoids relying on CoinGecko's USDT/USD if the goal is a specific IRR market rate.
    # The admin should be responsible for updating MANUAL_USD_TO_IRR_RATE.
    # If CoinGecko IRR is available, it's preferred.
    # If not, we use the manual rate directly as 1 USDT = X IRR.
    # This means MANUAL_USD_TO_IRR_RATE should be interpreted as USDT_TO_IRR_RATE
    # Let's rename MANUAL_USD_TO_IRR_RATE to MANUAL_USDT_TO_IRR_RATE for clarity for this fallback

    # Re-evaluating the fallback: The issue asks for REAL-TIME price.
    # A manual rate is not real-time.
    # If CoinGecko USDT/IRR is not available, we should inform the user.
    # The USDT/USD route is more of a peg check.
    # For now, if direct USDT/IRR fails, we indicate that.
    # A more robust solution might involve multiple price sources or admin-updated rates.

    # Let's keep it simple: try direct, if fails, then it fails for now for MVP.
    # The print statements in get_usdt_to_irr_price() will indicate the failure.
    return None, "Failed to fetch price from CoinGecko."
