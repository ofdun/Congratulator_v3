from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup
from const import *
import os
from threading import Thread
from time import sleep

TOKEN = os.getenv("TOKEN")
bot = TeleBot(TOKEN)


@bot.message_handler(commands=["start", "help"])
def start_message(message: Message) -> None:
    markup = customize_markup("Поздравь меня🥳")
    chat_id = message.chat.id
    name = message.from_user.first_name
    bot.send_message(
        chat_id=chat_id, text=WELCOME_MESSAGE.format(name=name), reply_markup=markup
    )


@bot.message_handler(content_types=["text"])
def main(message: Message) -> None:
    markup = customize_markup(
        "Поздравь меня🥳", "Ура!🎉"  # , "Подключить рассылку📬", "Отключить рассылку📬"
    )
    chat_id = message.chat.id
    bot.send_message(chat_id=chat_id, text="Test", reply_markup=markup)


def customize_markup(*button_names) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # Algorithm to make 2 btns per 1 row

    # for i in range(0, ceil(len(button_names) / 2) + 1, 2):
    #     try:
    #         markup.row(
    #             KeyboardButton(button_names[i]), KeyboardButton(button_names[i + 1])
    #         )
    #     except IndexError:
    #         markup.add(KeyboardButton(button_names[i]))

    markup.add(*button_names)
    return markup


def start_nonestop_poling():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            sleep(5)


if __name__ == "__main__":
    Thread(target=start_nonestop_poling).start()
