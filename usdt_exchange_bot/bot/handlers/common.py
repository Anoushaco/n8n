from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from ..models.user import User
from ..database import get_db # To access the database session
from ..utils.commission import get_commission_details_text # Add this import at the top
from ..utils.price import get_usdt_to_irr_price # Add this import at the top

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued and registers the user."""
    if update.message is None or update.message.from_user is None:
        # This can happen with some types of updates, though less common for commands
        await update.message.reply_text("Could not identify user.")
        return

    tg_user = update.message.from_user
    db: Session
    for db_session in get_db(): # Iterate to get the db session from the generator
        db = db_session
        break # We only need one session

    # Check if user exists
    user = db.query(User).filter(User.telegram_id == tg_user.id).first()

    welcome_message = ""

    if not user:
        new_user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        welcome_message = (
            f"Welcome to the P2P USDT Exchange Bot, {tg_user.first_name}!\n"
            "You have been registered. You can now start buying or selling USDT.\n"
            "Use /help to see available commands."
        )
        print(f"New user registered: {new_user}")
    else:
        welcome_message = (
            f"Welcome back, {tg_user.first_name}!\n"
            "Use /help to see available commands."
        )
        print(f"User already exists: {user}")

    if update.message:
        await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is issued."""
    help_text = (
        "Available commands:\n"
        "/start - Register and start the bot\n"
        "/price - Get current USDT price\n"
        "/buy <IRR_amount> - Place a buy order for USDT\n"
        "/sell <USDT_amount> - Place a sell order for USDT\n"
        "/calculator - Calculate commission for a trade\n"
        "/orders - View your active orders\n"
        "/cancel <order_id> - Cancel an order\n"
        # Add more commands as they are implemented
    )
    if update.message:
        await update.message.reply_text(help_text)

async def calculator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /calculator command.
    If an amount is provided, it calculates and shows the commission.
    Otherwise, it prompts the user to provide an amount.
    """
    if not update.message or not update.message.text:
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Please provide a USDT amount to calculate the commission.\n"
            "Usage: /calculator <USDT_amount>"
        )
        return

    usdt_amount_str = args[0]
    reply_text = get_commission_details_text(usdt_amount_str)
    await update.message.reply_text(reply_text)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /price command and displays the current USDT to IRR price."""
    if not update.message:
        return

    price_irr = get_usdt_to_irr_price() # Using the direct attempt first

    if price_irr:
        reply_text = f"Current price: 1 USDT = {price_irr} IRR (Source: CoinGecko)"
    else:
        # Fallback to USDT/USD and a manually defined USD/IRR rate as a placeholder
        # This part needs a configurable USD_TO_IRR rate in config.py
        # For now, let's indicate direct failure.
        # A better MVP might be to fetch USDT/USD and let admin set USD/IRR.
        # Or, if CoinGecko IRR is unreliable, bot owner must provide a stable source.
        # The current get_usdt_price_in_irr_preferred() in price.py is a bit complex for the handler.
        # Let's simplify the handler to just use get_usdt_to_irr_price()

        # price_info, source_info = get_usdt_price_in_irr_preferred() # This was the more complex one
        # if price_info:
        #    reply_text = f"Current price: 1 USDT = {price_info} IRR (Source: {source_info})"
        # else:
        #    reply_text = "Sorry, could not fetch the current USDT price. Please try again later."

        # Simpler message for direct failure:
        reply_text = "Sorry, could not fetch the current USDT to IRR price from CoinGecko. Please try again later."


    await update.message.reply_text(reply_text)
