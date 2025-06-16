from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ..models.user import User
from ..models.order import Order
from ..database import get_db
from ..utils.price import get_usdt_to_irr_price
from ..utils.commission import calculate_commission_usdt

async def buy_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /buy command to create a USDT buy order."""
    if not update.message or not update.message.from_user :
        # Added a check for update.message before trying to reply to it.
        print("Buy command received without message or user info.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /buy <IRR_amount>\n"
            "Example: /buy 50000000 (to buy 50,000,000 IRR worth of USDT)"
        )
        return

    tg_user = update.message.from_user

    try:
        irr_amount_to_spend = Decimal(context.args[0])
        if irr_amount_to_spend <= Decimal("0"):
            await update.message.reply_text("Please enter a positive amount in IRR.")
            return
    except InvalidOperation:
        await update.message.reply_text("Invalid IRR amount. Please enter a numeric value.")
        return

    db: Session
    # A bit safer way to get the session
    db_gen = None # Initialize to ensure it's defined for finally block
    try:
        db_gen = get_db()
        db = next(db_gen)
    except Exception as e:
        await update.message.reply_text("Error accessing database. Please try again later.")
        print(f"Failed to get DB session: {e}")
        return

    try:
        # Ensure user is registered
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()
        if not user:
            await update.message.reply_text("Please /start the bot first to register.")
            return

        # 1. Fetch current USDT/IRR price
        current_usdt_irr_price = get_usdt_to_irr_price()
        if not current_usdt_irr_price:
            await update.message.reply_text(
                "Sorry, could not fetch the current USDT price. Cannot create a buy order at this time. Please try again later."
            )
            return

        # 2. Calculate how much USDT can be bought with the IRR amount (before commission)
        usdt_amount_gross = (irr_amount_to_spend / current_usdt_irr_price).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP) # Higher precision for intermediate

        # 3. Calculate commission on the gross USDT amount
        commission_usdt, commission_rate = calculate_commission_usdt(usdt_amount_gross) # Expects Decimal

        # 4. Calculate net USDT amount the user will receive
        usdt_amount_net = usdt_amount_gross - commission_usdt

        if usdt_amount_net <= Decimal("0"):
            await update.message.reply_text(
                f"The calculated USDT amount after commission is too low or zero (Gross USDT: {usdt_amount_gross:.6f}, Commission: {commission_usdt:.6f} USDT). "
                "Please try with a larger IRR amount."
            )
            return

        # 5. Create and save the buy order
        new_buy_order = Order(
            user_id=user.id,
            order_type='buy',
            usdt_amount=usdt_amount_net.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            irr_amount=irr_amount_to_spend.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            commission_applied=commission_usdt.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            status='pending'
        )
        db.add(new_buy_order)
        try:
            db.commit()
            db.refresh(new_buy_order)
        except Exception as e:
            db.rollback()
            await update.message.reply_text("Could not save your buy order due to a database error. Please try again.")
            print(f"Error committing buy order: {e}")
            return


        # 6. Confirm order creation to the user
        confirmation_message = (
            f"✅ Buy Order Created Successfully!\n\n"
            f"Order ID: {new_buy_order.id}\n"
            f"------------------------------------\n"
            f"You are buying (Net): {new_buy_order.usdt_amount} USDT\n"
            f"You will pay: {new_buy_order.irr_amount} IRR\n"
            f"------------------------------------\n"
            f"Market Rate Used: 1 USDT = {current_usdt_irr_price} IRR\n"
            f"Gross USDT (before fee): {usdt_amount_gross.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)} USDT\n"
            f"Commission Rate: {commission_rate*100:.1f}%\n"
            f"Commission Fee: {new_buy_order.commission_applied} USDT\n"
            f"------------------------------------\n"
            f"Status: {new_buy_order.status}\n\n"
            f"We will notify you when a seller is matched."
        )
        await update.message.reply_text(confirmation_message)

        print(f"Buy order {new_buy_order.id} created for user {user.id} ({user.username}) for {new_buy_order.usdt_amount} USDT against {new_buy_order.irr_amount} IRR.")

    finally:
        if db_gen: # Ensure db_gen was assigned
            db.close() # Ensure session is closed
