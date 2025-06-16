from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ..models.user import User
from ..models.order import Order
from ..database import get_db
from ..utils.price import get_usdt_to_irr_price
from ..utils.commission import calculate_commission_usdt

async def sell_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /sell command to create a USDT sell order."""
    if not update.message or not update.message.from_user:
        print("Sell command received without message or user info.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /sell <USDT_amount>\n"
            "Example: /sell 100 (to sell 100 USDT)"
        )
        return

    tg_user = update.message.from_user

    try:
        usdt_amount_to_sell_gross = Decimal(context.args[0])
        if usdt_amount_to_sell_gross <= Decimal("0"):
            await update.message.reply_text("Please enter a positive amount of USDT to sell.")
            return
    except InvalidOperation:
        await update.message.reply_text("Invalid USDT amount. Please enter a numeric value.")
        return

    db: Session
    db_gen = None # Initialize for finally block
    try:
        db_gen = get_db()
        db = next(db_gen)
    except Exception as e:
        await update.message.reply_text("Error accessing database. Please try again later.")
        print(f"Failed to get DB session: {e}")
        return

    try:
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()
        if not user:
            await update.message.reply_text("Please /start the bot first to register.")
            return

        # 1. Fetch current USDT/IRR price
        current_usdt_irr_price = get_usdt_to_irr_price()
        if not current_usdt_irr_price:
            await update.message.reply_text(
                "Sorry, could not fetch the current USDT price. Cannot create a sell order at this time. Please try again later."
            )
            return

        # 2. Calculate commission on the gross USDT amount being sold
        commission_usdt, commission_rate = calculate_commission_usdt(usdt_amount_to_sell_gross)

        net_usdt_after_commission_for_seller_calculation = usdt_amount_to_sell_gross - commission_usdt

        if net_usdt_after_commission_for_seller_calculation <= Decimal("0"):
            await update.message.reply_text(
                f"The calculated commission ({commission_usdt:.6f} USDT) is greater than or equal to the amount you want to sell "
                f"({usdt_amount_to_sell_gross:.6f} USDT). Please try with a larger USDT amount."
            )
            return

        # 4. Calculate IRR amount the seller will receive for the gross USDT
        irr_amount_for_order = (usdt_amount_to_sell_gross * current_usdt_irr_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


        # 5. Create and save the sell order
        new_sell_order = Order(
            user_id=user.id,
            order_type='sell',
            usdt_amount=usdt_amount_to_sell_gross.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            irr_amount=irr_amount_for_order,
            commission_applied=commission_usdt.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            status='pending'
        )
        db.add(new_sell_order)
        try:
            db.commit()
            db.refresh(new_sell_order)
        except Exception as e:
            db.rollback()
            await update.message.reply_text("Could not save your sell order due to a database error. Please try again.")
            print(f"Error committing sell order: {e}")
            return

        # 6. Confirm order creation to the user
        irr_value_after_commission = (net_usdt_after_commission_for_seller_calculation * current_usdt_irr_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        confirmation_message = (
            f"✅ Sell Order Created Successfully!\n\n"
            f"Order ID: {new_sell_order.id}\n"
            f"------------------------------------\n"
            f"You are selling: {new_sell_order.usdt_amount} USDT\n"
            f"A buyer will pay: {new_sell_order.irr_amount} IRR for this amount.\n"
            f"------------------------------------\n"
            f"Market Rate Used: 1 USDT = {current_usdt_irr_price} IRR\n"
            f"Commission Rate: {commission_rate*100:.1f}%\n"
            f"Commission Fee: {new_sell_order.commission_applied} USDT (valued at approx. {(new_sell_order.commission_applied * current_usdt_irr_price).quantize(Decimal('0.01'))} IRR)\n"
            f"Net IRR you will receive (approx.): {irr_value_after_commission} IRR\n"
            f"------------------------------------\n"
            f"Status: {new_sell_order.status}\n\n"
            f"We will notify you when a buyer is matched."
        )
        await update.message.reply_text(confirmation_message)

        print(f"Sell order {new_sell_order.id} created for user {user.id} ({user.username}) for {new_sell_order.usdt_amount} USDT, expecting {new_sell_order.irr_amount} IRR.")

    finally:
        if db_gen:
            db.close()
