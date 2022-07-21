import os
import telebot
import requests
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

WEATHER_API_TOKEN = os.getenv('WEATHER_API_TOKEN')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
bot = telebot.TeleBot(BOT_API_TOKEN)
parameters = {
    'key': WEATHER_API_TOKEN,
    'place_id': 'berdychiv',
}

today_is = datetime.now().strftime('%d.%m.%Y')
url_privatbank = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={today_is}'
url = 'https://www.meteosource.com/api/v1/free/point'
data_privatbank = requests.get(url_privatbank).json()
data = requests.get(url, parameters).json()


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
        text = f"Now in Berdychiv temperature is {data['current']['temperature']}"

        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text)
    elif message.text == '💵 Currency':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        text = 'You can only convert USD/EUR/PLN currency into UAH or see the purchase rate of the National Bank of Ukraine'
        available_currency = telebot.types.KeyboardButton('💰 All available currency')
        dollar = telebot.types.KeyboardButton('🇺🇸 Dollar')
        euro = telebot.types.KeyboardButton('🇪🇺 Euro')
        zloty = telebot.types.KeyboardButton('🇵🇱 Zloty')
        previous = telebot.types.KeyboardButton('🔙 Go to the main menu')

        markup.add(available_currency, dollar, euro, zloty, previous)
        bot.send_message(message.chat.id, text, reply_markup=markup)
    elif message.text == '💸 Cryptocurrency':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        text = 'Choose which cryptocurrency you wanna see'
        bitcoin = telebot.types.KeyboardButton('Bitcoin')
        ethereum = telebot.types.KeyboardButton('Ethereum')
        dogecoin = telebot.types.KeyboardButton('Dogecoin')
        solana = telebot.types.KeyboardButton('Solana')
        previous = telebot.types.KeyboardButton('🔙 Go to the main menu')

        markup.add(bitcoin, ethereum, dogecoin, solana, previous)
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text, reply_markup=markup)
    elif message.text == '💰 All available currency':
        euro_currency = data_privatbank['exchangeRate'][8]
        zloty_currency = data_privatbank['exchangeRate'][17]
        dollar_currency = data_privatbank['exchangeRate'][24]
        text = (
            f"Currency: {dollar_currency['currency']} | Purchase National Bank: {dollar_currency['purchaseRateNB']:.2f} | "
            f"Sale National Bank {dollar_currency['saleRateNB']:.2f} | Purchase: {dollar_currency['purchaseRate']:.2f} | "
            f"Sale: {dollar_currency['saleRate']:.2f}\n"
            f"Currency: {euro_currency['currency']} | Purchase National Bank: {euro_currency['purchaseRateNB']:.2f} | "
            f"Sale National Bank {euro_currency['saleRateNB']:.2f} | Purchase: {euro_currency['purchaseRate']:.2f} | "
            f"Sale: {euro_currency['saleRate']:.2f}\n"
            f"Currency: {zloty_currency['currency']} | Purchase National Bank: {zloty_currency['purchaseRateNB']:.2f} | "
            f"Sale National Bank {zloty_currency['saleRateNB']:.2f} | Purchase: {zloty_currency['purchaseRate']:.2f} | "
            f"Sale: {zloty_currency['saleRate']:.2f}"
        )

        bot.send_message(message.chat.id, text)
    elif message.text == '🇺🇸 Dollar':
        text = bot.send_message(message.chat.id, 'Enter the number')

        bot.register_next_step_handler(text, currency_convert, data_privatbank['exchangeRate'][24]['purchaseRateNB'])
    elif message.text == '🇪🇺 Euro':
        text = bot.send_message(message.chat.id, 'Enter the number')

        bot.register_next_step_handler(text, currency_convert, data_privatbank['exchangeRate'][8]['purchaseRateNB'])
    elif message.text == '🇵🇱 Zloty':
        text = bot.send_message(message.chat.id, 'Enter the number')

        bot.register_next_step_handler(text, currency_convert, data_privatbank['exchangeRate'][17]['purchaseRateNB'])
    elif message.text == '🔙 Go to the main menu':
        text = "You're returned to the main menu."

        bot.send_message(message.from_user.id, text, reply_markup=main_menu_markup())


def currency_convert(message: telebot.types.Message, currency: float) -> None:
    try:
        result = float(message.text) * currency
        bot.send_message(message.chat.id, f'{result:.2f}')
    except ValueError:
        bot.send_message(message.chat.id, 'You have entered an incorrect value for currency conversion. Please enter the correct value!')


bot.infinity_polling()
