import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import aiohttp
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize SQLite database
conn = sqlite3.connect('story_validator_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Create table to store user data if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_data (
    user_id INTEGER PRIMARY KEY,
    validator_address TEXT,
    node_endpoint TEXT
)
''')
conn.commit()

# Define commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.message.from_user.id
    cursor.execute('SELECT validator_address, node_endpoint FROM user_data WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result:
        validator_address, node_endpoint = result
        message = "Welcome back to the Story Validator Bot by Rage!\n"
        if validator_address:
            message += f"✅ Validator Address: {validator_address}\n"
        if node_endpoint:
            message += f"✅ Node Endpoint: {node_endpoint}\n"
        message += "\nYou can use the buttons below to update or check your validator and node status."
    else:
        message = "👋 Welcome to the Story Validator Bot by Rage! 🚀 Please use the buttons below to add a validator or node RPC to get started:"
    
    keyboard = [
        ["Add Validator Address"],
        ["Add Node Endpoint"],
        ["Check Validator Status"],
        ["Check Node Status"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def add_validator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to add a validator address."""
    await update.message.reply_text("Please enter your validator address:")

async def save_validator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save the user's validator address and show validator details."""
    validator_address = update.message.text.strip()
    user_id = update.message.from_user.id
    cursor.execute('UPDATE user_data SET validator_address = ? WHERE user_id = ?', (validator_address, user_id))
    if cursor.rowcount == 0:
        cursor.execute('INSERT INTO user_data (user_id, validator_address) VALUES (?, ?)', (user_id, validator_address))
    conn.commit()
    await update.message.reply_text("Validator address saved successfully.")
    await show_validator_details(update, context)

async def add_node(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to add a node endpoint with full URL."""
    await update.message.reply_text("Please enter your node endpoint URL (e.g., http://144.76.112.120:26657/):")

async def save_node(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if the user's node endpoint is reachable and then save it if valid."""
    node_endpoint = update.message.text.strip()
    user_id = update.message.from_user.id
    if not node_endpoint.endswith('/'):
        node_endpoint += '/'  # Ensure the endpoint URL ends with a slash
    node_status_url = f"{node_endpoint}status"

    # Log the node endpoint being tested
    logger.info(f"Testing node endpoint: {node_status_url}")

    # Check if the node endpoint is reachable before saving
    async with aiohttp.ClientSession() as session:
        try:
            # Check node information using /status endpoint
            async with session.get(node_status_url, timeout=10) as response:
                if response.status == 404:
                    await update.message.reply_text("Error: The /status endpoint is not found. Please ensure the endpoint URL is correct.")
                    return
                data = await response.json()
                logger.info(f"Node status response: {data}")
                if response.status != 200:
                    await update.message.reply_text("Error: The provided node endpoint is not reachable. Please enter a valid endpoint.")
                    return

            # If the check passes, save the endpoint
            cursor.execute('UPDATE user_data SET node_endpoint = ? WHERE user_id = ?', (node_endpoint, user_id))
            if cursor.rowcount == 0:
                cursor.execute('INSERT INTO user_data (user_id, node_endpoint) VALUES (?, ?)', (user_id, node_endpoint))
            conn.commit()
            await update.message.reply_text("Node endpoint saved successfully.")
            await show_node_status(update, context)  # Show node status after saving successfully
        except aiohttp.ClientConnectorError as e:
            await update.message.reply_text(f"Error: Unable to connect to the provided node endpoint. Please enter a valid endpoint. ({str(e)})")
            logger.error(f"ClientConnectorError reaching node endpoint: {str(e)}")
        except aiohttp.ClientResponseError as e:
            await update.message.reply_text(f"Error: Received an unexpected response from the node endpoint. ({str(e)})")
            logger.error(f"ClientResponseError: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"Error: Unable to reach the provided node endpoint. Please enter a valid endpoint. ({str(e)})")
            logger.error(f"Error reaching node endpoint: {str(e)}")
            return

async def show_validator_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the status of the validator."""
    user_id = update.message.from_user.id
    cursor.execute('SELECT validator_address FROM user_data WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        await update.message.reply_text("Validator address not found. Please add a validator using the button.")
        return

    validator_address = result[0]
    api_url = f"https://api.testnet.storyscan.app/validators/{validator_address}"

    try:
        response = requests.get(api_url)
        data = response.json()
        logger.info(f"Validator details response: {data}")

        if response.status_code == 200:
            # Extracting relevant validator details
            moniker = data.get("moniker", "N/A")
            operator_address = data.get("operator_address", "N/A")
            total_staked = data.get("tokens", "N/A")
            commission_rate = data.get("commission", {}).get("commission_rates", {}).get("rate", "N/A")
            jailed = data.get("signingInfo", {}).get("tombstoned", False)
            voting_power_percent = data.get("votingPowerPercent", "N/A")
            success_blocks = data.get("uptime", {}).get("historicalUptime", {}).get("successBlocks", "N/A")
            consensus_pubkey_hex = data.get("consensusAddress", "N/A")

            # Fetch missed blocks count from slashing API using consensus pubkey (hex)
            slashing_api_url = f"https://api-story-testnet.trusted-point.com/cosmos/slashing/v1beta1/signing_infos/{consensus_pubkey_hex}"
            slashing_response = requests.get(slashing_api_url)
            slashing_data = slashing_response.json()
            logger.info(f"Slashing info response: {slashing_data}")
            missed_blocks = slashing_data.get("val_signing_info", {}).get("missed_blocks_counter", "N/A")

            # Format the validator status message
            status_message = (
                f"Validator Status:\n"
                f"Moniker: {moniker}\n"
                f"Operator Address: {operator_address}\n"
                f"Total Staked: {total_staked}\n"
                f"Commission Rate: {commission_rate}\n"
                f"Jailed: {'Yes' if jailed else 'No'}\n"
                f"Voting Power: {voting_power_percent}\n"
                f"Successful Blocks: {success_blocks}\n"
                f"Missed Blocks: {missed_blocks}"
            )
        else:
            status_message = "Error fetching validator status. Please check the validator address."
    except Exception as e:
        status_message = f"An error occurred: {str(e)}"
        logger.error(f"Error fetching validator details: {str(e)}")
    
    await update.message.reply_text(status_message)

# Show Node Status Function
async def show_node_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the status of the node."""
    user_id = update.message.from_user.id
    cursor.execute('SELECT node_endpoint FROM user_data WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        await update.message.reply_text("Node endpoint not found. Please add a node using the button.")
        return

    node_endpoint = result[0]
    node_status_url = f"{node_endpoint}status"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(node_status_url) as response:
                if response.status == 404:
                    await update.message.reply_text("Error: The /status endpoint is not found. Please ensure the endpoint URL is correct.")
                    return
                data = await response.json()
                logger.info(f"Node status response: {data}")
                if response.status != 200:
                    await update.message.reply_text("Error: Unable to reach the provided node endpoint. Please enter a valid endpoint.")
                    return

            # Extracting node status details
            sync_info = data.get("result", {}).get("sync_info", {})
            latest_block_height = sync_info.get("latest_block_height", "N/A")
            latest_block_time = sync_info.get("latest_block_time", "N/A")
            catching_up = sync_info.get("catching_up", "N/A")
            moniker = data.get("result", {}).get("node_info", {}).get("moniker", "N/A")
            network_name = data.get("result", {}).get("node_info", {}).get("network", "N/A")

            # Assuming the network block height is the same as the latest block height of the sync_info
            network_block_height = latest_block_height

            # Format the node status message with emojis for better visualization
            status_message = (
                f"🔍 <b>Node Status</b>:\n"
                f"🔸 <b>Moniker</b>: {moniker}\n"
                f"📊 <b>Your Block Height</b>: {latest_block_height}\n"
                f"🌐 <b>Network Block Height</b>: {network_block_height}\n"
                f"🛧 <b>Network Name</b>: {network_name}\n"
                f"⏱️ <b>Latest Block Time</b>: {latest_block_time}\n"
                f"📈 <b>Catching Up</b>: {'Yes' if catching_up else 'No'}"
            )
        except Exception as e:
            status_message = f"An error occurred: {str(e)}"
            logger.error(f"Error fetching node status: {str(e)}")

    await update.message.reply_text(status_message, parse_mode='HTML')

# Adding handlers and main function to run the bot
if __name__ == '__main__':
    # Use the token from the .env file
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Adding command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^(Add Validator Address)$"), add_validator))
    application.add_handler(MessageHandler(filters.Regex("^(Add Node Endpoint)$"), add_node))
    application.add_handler(MessageHandler(filters.Regex("^(Check Validator Status)$"), show_validator_details))
    application.add_handler(MessageHandler(filters.Regex("^(Check Node Status)$"), show_node_status))
    application.add_handler(MessageHandler(filters.Regex("^[a-zA-Z0-9]+$"), save_validator))
    application.add_handler(MessageHandler(filters.Regex(r"^http://\d{1,3}(\.\d{1,3}){3}:\d{4,5}/$"), save_node))

    # Run the bot until Ctrl-C is pressed
    application.run_polling()
