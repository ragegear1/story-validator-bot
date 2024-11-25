# Story Validator Bot

This repository contains a Telegram bot that helps users monitor their Story node and validator setup. The bot allows you to add your node endpoint and validator address, and easily check their statuses.

## Features

- **Add Validator Address**: Easily add your validator address and save it for future checks.
- **Add Node Endpoint**: Add your node endpoint and save it, allowing the bot to verify and monitor its status.
- **Check Validator Status**: Quickly check the status of your validator, including key metrics such as total staked tokens, commission rate, and missed blocks.
- **Check Node Status**: Get detailed information on your node's status, such as block height, network sync status, and more.
- **User-Friendly Interface**: The bot provides an interactive interface using Telegram keyboard buttons to make it easy to manage your node and validator.

## Getting Started

### Prerequisites

- Python 3.8+
- A Telegram bot token (you can get one by talking to [@BotFather](https://t.me/BotFather) on Telegram)
- SQLite for storing user data

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/story-validator-bot.git
   cd story-validator-bot
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your Telegram bot token:

   ```
   BOT_TOKEN=your_telegram_bot_token
   ```

4. Run the bot:

   ```bash
   python story_validator_bot.py
   ```

## Usage

Once the bot is running, you can interact with it on Telegram by clicking **Start**. The bot will guide you through adding your validator address and node endpoint. You can then use the provided buttons to check the status of your setup.

### Available Commands

- `/start` - Start interacting with the bot and get the available options.
- **Add Validator Address** - Add your validator address.
- **Add Node Endpoint** - Add your node endpoint URL.
- **Check Validator Status** - Check the current status of your validator.
- **Check Node Status** - Check the current status of your node.

## Development

Feel free to contribute to the project by submitting a pull request. Any feedback or suggestions are highly appreciated!

### Logging

The bot uses Python's `logging` module to log important events and errors, which can help in debugging and improving the bot.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Feedback

If you encounter any issues or have suggestions for improvements, feel free to open an issue or reach out on Telegram.

## Acknowledgements

- Thanks to [@BotFather](https://t.me/BotFather) for making it easy to create Telegram bots.
- Special thanks to the Story project community for their support and feedback.

