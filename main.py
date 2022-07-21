import os
import telebot
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_TOKEN = os.getenv('WEATHER_API_TOKEN')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
bot = telebot.TeleBot(BOT_API_TOKEN)
weather_parameters = {
    'key': WEATHER_API_TOKEN,
    'place_id': 'berdychiv',
}
crypto_headers = {
    'accept': 'application/json',
}

crypto_url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd'
privatbank_url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={datetime.now().strftime('%d.%m.%Y')}"
weather_url = 'https://www.meteosource.com/api/v1/free/point'
privatbank_data = requests.get(privatbank_url).json()
weather_data = requests.get(weather_url, params=weather_parameters).json()
cryptocurrency_data = requests.get(crypto_url, headers=crypto_headers).json()
cryptocurrency_list = [cryptocurrency for cryptocurrency in cryptocurrency_data]
country_codes = {
    'US': '🇺🇸',
    'PL': '🇵🇱',
    'EU': '🇪🇺',
}


def which_season(current_month: int) -> str:
    match current_month:
        case 12 | 1 | 2:
            return '❄'
        case 3 | 4 | 5:
            return '🌺'
        case 6 | 7 | 8:
            return '☀'
        case 9 | 10 | 11:
            return '🍁'


def main_menu_markup() -> telebot.types.ReplyKeyboardMarkup:
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    weather = telebot.types.KeyboardButton(f'{which_season(datetime.now().month)} Weather')
    currency = telebot.types.KeyboardButton('💵 Currency')
    cryptocurrency = telebot.types.KeyboardButton('💸 Cryptocurrency')

    markup.add(weather, currency, cryptocurrency)
    return markup


@bot.message_handler(commands=['start'])
def user_greetings(message: telebot.types.Message) -> None:
    user = message.from_user
    text = f'Greetings, @{user.username}.'

    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, text, reply_markup=main_menu_markup())


@bot.message_handler(content_types=['text'])
def bot_message(message: telebot.types.Message) -> None:
    if message.text == f'{which_season(datetime.now().month)} Weather':
        text = f"Now in Berdychiv temperature is {weather_data['current']['temperature']}"

        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text)
    elif message.text == '💵 Currency':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        text = 'You can only convert USD/EUR/PLN currency into UAH or see the purchase rate of the National Bank of Ukraine'
        available_currency = telebot.types.KeyboardButton('💰 All available currency')
        dollar = telebot.types.KeyboardButton(f"{country_codes['US']} Dollar")
        euro = telebot.types.KeyboardButton(f"{country_codes['EU']} Euro")
        zloty = telebot.types.KeyboardButton(F"{country_codes['PL']} Zloty")
        previous = telebot.types.KeyboardButton('🔙 Go to the main menu')

        markup.add(available_currency, dollar, euro, zloty, previous)
        bot.send_message(message.chat.id, text, reply_markup=markup)
    elif message.text == '💸 Cryptocurrency':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        text = 'Choose which cryptocurrency you wanna see'
        available_cryptocurrency = telebot.types.KeyboardButton('💰 All available cryptocurrency')
        bitcoin = telebot.types.KeyboardButton('Bitcoin')
        ethereum = telebot.types.KeyboardButton('Ethereum')
        dogecoin = telebot.types.KeyboardButton('Dogecoin')
        solana = telebot.types.KeyboardButton('Solana')
        previous = telebot.types.KeyboardButton('🔙 Go to the main menu')

        markup.add(available_cryptocurrency, bitcoin, ethereum, dogecoin, solana, previous)
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text, reply_markup=markup)
    elif message.text == '💰 All available currency':
        text = '\n'.join((
            f"<pre>Currency: {currency['currency']} | Purchase National Bank: {currency['purchaseRateNB']:5.2f} | "
            f"Sale National Bank: {currency['saleRateNB']:5.2f} | Purchase: {currency['purchaseRate']:5.2f} | "
            f"Sale: {currency['saleRate']:5.2f}</pre>"
        ) for currency in privatbank_data['exchangeRate'][1:] if currency['currency'] in ['USD', 'EUR', 'PLN'])

        bot.send_message(message.chat.id, text, parse_mode='html')
    elif message.text == f"{country_codes['US']} Dollar":
        text = bot.send_message(message.chat.id, 'Enter the number')

        bot.register_next_step_handler(
            text, currency_convert, privatbank_data['exchangeRate'][24]['purchaseRateNB'], country_codes['US']
        )
    elif message.text == f"{country_codes['EU']} Euro":
        text = bot.send_message(message.chat.id, 'Enter the number')

        bot.register_next_step_handler(
            text, currency_convert, privatbank_data['exchangeRate'][8]['purchaseRateNB'], country_codes['EU']
        )
    elif message.text == f"{country_codes['PL']} Zloty":
        text = bot.send_message(message.chat.id, 'Enter the number')

        bot.register_next_step_handler(
            text, currency_convert, privatbank_data['exchangeRate'][17]['purchaseRateNB'], country_codes['PL']
        )
    elif message.text == '🔙 Go to the main menu':
        text = "You're returned to the main menu."

        bot.send_message(message.from_user.id, text, reply_markup=main_menu_markup())
    elif message.text == '💰 All available cryptocurrency':
        text = '\n'.join((
                f"<pre>Cryptocurrency: {cryptocurrency['name']:8} / {cryptocurrency['symbol'].upper():4} | "
                f"Price: {cryptocurrency['current_price']:.2f}</pre>"
            ) for cryptocurrency in cryptocurrency_list if cryptocurrency['symbol'] in ['btc', 'eth', 'sol', 'doge']
        )

        bot.send_message(message.chat.id, text, parse_mode='html')
    elif message.text in [cryptocurrency['name'] for cryptocurrency in cryptocurrency_list]:
        text = bot.send_message(message.chat.id, 'Enter the number')
        data = [cryptocurrency for cryptocurrency in cryptocurrency_list if cryptocurrency['name'] == message.text]

        bot.register_next_step_handler(text, cryptocurrency_convert, data)


def currency_convert(message: telebot.types.Message, currency: float, country_code: str) -> None:
    try:
        result = float(message.text) * currency

        bot.send_message(message.chat.id, f'{country_code} {result:.2f}')
    except ValueError:
        bot.send_message(
            message.chat.id, 'You have entered an incorrect value for currency conversion. Please enter the correct value!'
        )


def cryptocurrency_convert(message: telebot.types.Message, cryptocurrency: tuple) -> None:
    try:
        result = float(message.text) * cryptocurrency[0]['current_price']
        text = (
            cryptocurrency[0]['image'],
            f"{cryptocurrency[0]['symbol'].upper()}: {result:.2f}"
        )

        bot.send_photo(message.chat.id, photo=text[0], caption=text[1])
    except ValueError:
        bot.send_message(
            message.chat.id, 'You have entered an incorrect value for currency conversion. Please enter the correct value!'
        )


bot.infinity_polling()
