from decimal import Decimal, ROUND_HALF_UP

# Define commission tiers
# Using Decimal for precision with currency
COMMISSION_TIERS = [
    {"min_usdt": Decimal("0"), "max_usdt": Decimal("10000"), "rate": Decimal("0.025")},  # 2.5%
    {"min_usdt": Decimal("10000"), "max_usdt": Decimal("50000"), "rate": Decimal("0.015")}, # 1.5%
    {"min_usdt": Decimal("50000"), "max_usdt": Decimal("Infinity"), "rate": Decimal("0.010")}, # 1.0%
]

def calculate_commission_usdt(usdt_amount: Decimal) -> tuple[Decimal, Decimal]:
    """
    Calculates the commission amount in USDT and the rate applied based on the USDT transaction amount.

    Args:
        usdt_amount (Decimal): The amount of USDT for the transaction.

    Returns:
        tuple[Decimal, Decimal]: A tuple containing:
            - commission_usdt (Decimal): The calculated commission in USDT.
            - commission_rate (Decimal): The commission rate applied (e.g., 0.025 for 2.5%).
    """
    if not isinstance(usdt_amount, Decimal):
        try:
            usdt_amount = Decimal(str(usdt_amount))
        except Exception:
            raise ValueError("USDT amount must be a number or Decimal.")

    if usdt_amount < Decimal("0"):
        raise ValueError("USDT amount cannot be negative.")

    applicable_tier = None
    for tier in COMMISSION_TIERS:
        if tier["min_usdt"] <= usdt_amount < tier["max_usdt"]:
            applicable_tier = tier
            break

    # Fallback for amounts exactly at the boundary or above the last tier's min_usdt
    if applicable_tier is None and usdt_amount >= COMMISSION_TIERS[-1]["min_usdt"]:
        applicable_tier = COMMISSION_TIERS[-1]

    if applicable_tier is None:
        # This should ideally not happen if tiers are defined correctly from 0 to infinity
        raise ValueError("Could not determine commission tier for the given USDT amount.")

    commission_rate = applicable_tier["rate"]
    commission_usdt = usdt_amount * commission_rate

    # Quantize to a reasonable number of decimal places for USDT, e.g., 6
    # USDT TRC20 typically supports 6 decimal places.
    return commission_usdt.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), commission_rate

def get_commission_details_text(usdt_amount_str: str) -> str:
    """
    Provides a user-friendly string detailing the commission for a given USDT amount.
    Handles potential conversion errors.
    """
    try:
        usdt_amount = Decimal(usdt_amount_str)
        if usdt_amount <= Decimal("0"):
            return "Please enter a positive USDT amount."

        commission_usdt, rate = calculate_commission_usdt(usdt_amount)
        net_usdt_after_commission = usdt_amount - commission_usdt # For a seller

        return (
            f"Trade Amount: {usdt_amount.quantize(Decimal('0.000001'))} USDT\n"
            f"Commission Rate: {rate*100:.1f}%\n"
            f"Commission Fee: {commission_usdt.quantize(Decimal('0.000001'))} USDT\n"
            f"Net USDT (for seller after fee): {net_usdt_after_commission.quantize(Decimal('0.000001'))} USDT"
        )
    except ValueError as e:
        return str(e)
    except Exception:
        return "Invalid amount entered. Please enter a numeric value for USDT amount."
