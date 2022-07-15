import os
import telebot
import requests
from datetime import date
from dotenv import load_dotenv


load_dotenv()

WEATHER_API_TOKEN = os.getenv('WEATHER_API_TOKEN')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
bot = telebot.TeleBot(BOT_API_TOKEN)
parameters = {
    'key': WEATHER_API_TOKEN,
    'place_id': 'berdychiv',
}

url = 'https://www.meteosource.com/api/v1/free/point'
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


@bot.message_handler(commands=['start'])
def send_welcome(message: telebot.types.Message) -> None:
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    user = message.from_user
    text = f'Greetings, @{user.username}.'
    weather = telebot.types.KeyboardButton(f'{which_season(date.today().month)} Weather')

    markup.add(weather)
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(content_types=['text'])
def current_temperature(message: telebot.types.Message) -> None:
    if message.text == f'{which_season(date.today().month)} Weather':
        text = f"Now in Berdychiv temperature is {data['current']['temperature']}"

        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, text)


bot.infinity_polling()
