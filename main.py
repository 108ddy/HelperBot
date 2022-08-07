import os
import telebot
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request
from collections.abc import Callable

load_dotenv()

WEATHER_API_TOKEN = os.getenv('WEATHER_API_TOKEN')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
bot = telebot.TeleBot(BOT_API_TOKEN)
server = Flask(__name__)
crypto_headers = {
    'accept': 'application/json',
}

crypto_url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd'
privatbank_url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={datetime.now().strftime('%d.%m.%Y')}"
privatbank_data = requests.get(privatbank_url).json()
cryptocurrency_data = requests.get(crypto_url, headers=crypto_headers).json()
cryptocurrency_list = [cryptocurrency for cryptocurrency in cryptocurrency_data]
country_codes = {
    'US': '🇺🇸',
    'PL': '🇵🇱',
    'EU': '🇪🇺',
}


class CityDoesNotExist(Exception):
    pass


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


def get_city_weather_data(city: str = 'Berdychiv') -> tuple:
    weather_url = 'https://www.meteosource.com/api/v1/free/point'
    weather_parameters = {
        'key': WEATHER_API_TOKEN,
        'place_id': city.lower(),
    }

    weather_data = requests.get(weather_url, params=weather_parameters).json()

    return weather_data, city


def get_weather(data: Callable[[str], tuple]) -> str:
    try:
        current_weather_data = data[0]['current']
        city = data[1]
    except KeyError:
        raise CityDoesNotExist
    else:
        return (
            f"City: {city}\n"
            f"Temperature: {current_weather_data['temperature']}\n"
            f"Summary: {current_weather_data['summary']}\n"
            f"Wind: (Speed: {current_weather_data['wind']['speed']}, Angle: {current_weather_data['wind']['angle']})\n"
            f"Cloud cover: {current_weather_data['cloud_cover']}\n"
        )


def get_weather_to_the_same_day(data: Callable[[str], tuple]) -> str:
    text = ''
    weather_data = data[0]
    city = data[1]

    for hourly_weather_data in weather_data['hourly']['data']:
        text += (
            f"City: {city}\n"
            f"Time: {hourly_weather_data['date']}\n"
            f"Temperature: {hourly_weather_data['temperature']}\n"
            f"Summary: {hourly_weather_data['summary']}\n"
            f"Wind: (Speed: {hourly_weather_data['wind']['speed']}, Angle: {hourly_weather_data['wind']['angle']})\n"
            f"Cloud cover: {hourly_weather_data['cloud_cover']}\n\n"
        )

    return text


def main_menu_markup() -> telebot.types.ReplyKeyboardMarkup:
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    weather = telebot.types.KeyboardButton(f'{which_season(datetime.now().month)} Weather')
    currency = telebot.types.KeyboardButton('💵 Currency')
    cryptocurrency = telebot.types.KeyboardButton('💸 Cryptocurrency')

    markup.add(weather, currency, cryptocurrency)

    return markup


def get_city_weather(message: telebot.types.Message) -> None:
    try:
        weather_data = get_city_weather_data(message.text)
        text = get_weather(weather_data)
    except CityDoesNotExist:
        bot.send_message(message.chat.id, 'This city does not exist. Please enter an existing one.')
    else:
        bot.send_message(message.chat.id, text)


def cryptocurrency_convert(message: telebot.types.Message, cryptocurrency: tuple) -> None:
    try:
        result = float(message.text) * cryptocurrency[0]['current_price']
        text = (
            cryptocurrency[0]['image'],
            f"{cryptocurrency[0]['symbol'].upper()}: {result:.2f}$"
        )

        bot.send_photo(message.chat.id, photo=text[0], caption=text[1])
    except ValueError:
        bot.send_message(
            message.chat.id, 'You have entered an incorrect value for currency conversion. Please enter the correct value!'
        )


def currency_convert(message: telebot.types.Message, currency: float, country_code: str) -> None:
    try:
        result = float(message.text) * currency

        bot.send_message(message.chat.id, f'{country_code} {result:.2f}')
    except ValueError:
        bot.send_message(
            message.chat.id, 'You have entered an incorrect value for currency conversion. Please enter the correct value!'
        )


@bot.message_handler(commands=['start'])
def user_greetings(message: telebot.types.Message) -> None:
    user = message.from_user
    text = f'Greetings, @{user.username}.'
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, text, reply_markup=main_menu_markup())


@bot.message_handler(commands=['location'])
def location(message: telebot.types.Message) -> None:
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    current_location = telebot.types.KeyboardButton('Location', request_location=True)

    markup.add(current_location)
    bot.send_message(message.chat.id, f'Take location {message.location}', reply_markup=markup)


@bot.message_handler(content_types=['location'])
def get_location(message: telebot.types.Message) -> None:
    bot.delete_message(message.chat.id, message.id)
    print(message.id)
    print(message.location)


@bot.message_handler(content_types=['text'])
def bot_message(message: telebot.types.Message) -> None:
    if message.text == f'{which_season(datetime.now().month)} Weather':
        markup = telebot.types.InlineKeyboardMarkup()
        text = 'Use one of three button below'
        current_weather = telebot.types.InlineKeyboardButton(text='Current weather', callback_data='current_weather')
        city_weather = telebot.types.InlineKeyboardButton(text='Type the city which you wanna see', callback_data='city_weather')
        all_weather = telebot.types.InlineKeyboardButton(text='Display all weather from current to next day at the same time', callback_data='all_weather')

        markup.row_width = 1
        markup.add(current_weather, city_weather, all_weather)
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text, reply_markup=markup)
    elif message.text == '💵 Currency':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        text = 'You can only convert USD/EUR/PLN currency into UAH or see the purchase rate of the National Bank of Ukraine'
        available_currency = telebot.types.KeyboardButton('💰 All available currency')
        dollar = telebot.types.KeyboardButton(f"{country_codes['US']} Dollar")
        euro = telebot.types.KeyboardButton(f"{country_codes['EU']} Euro")
        zloty = telebot.types.KeyboardButton(f"{country_codes['PL']} Zloty")
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


@bot.callback_query_handler(func=lambda call: True)
def weather_variant(call: telebot.types.CallbackQuery) -> None:
    if call.data == 'current_weather':
        text = get_weather(get_city_weather_data())

        bot.send_message(call.message.chat.id, text)
    elif call.data == 'city_weather':
        text = bot.send_message(call.message.chat.id, 'Enter the city')

        bot.register_next_step_handler(text, get_city_weather)
    elif call.data == 'all_weather':
        text = get_weather_to_the_same_day(get_city_weather_data())

        bot.send_message(call.message.chat.id, text)


if 'HEROKU' in list(os.environ.keys()):
    @server.route('/' + BOT_API_TOKEN, methods=['POST'])
    def get_message() -> tuple:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_update([update])

        return '!', 200

    @server.route('/')
    def webhook() -> tuple:
        bot.remove_webhook()
        bot.set_webhook(url='https://helper108ddybot.herokuapp.com/' + BOT_API_TOKEN)

        return '!', 200

    server.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
else:
    bot.remove_webhook()
    bot.infinity_polling()
