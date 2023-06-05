from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup
from const import *
import os
from threading import Thread
from time import sleep
from datetime import datetime
from typing import List
from bs4 import BeautifulSoup as bs
import requests
from dataclasses import dataclass

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
    user_id = message.from_user.id
    user_is_mailing = check_if_user_is_mailing(user_id)

    if user_is_mailing:
        markup = customize_markup(
            "Поздравь меня🥳", "Ура!🎉", "Отключить рассылку📬")
    else:
        markup = customize_markup(
            "Поздравь меня🥳", "Ура!🎉", "Подключить рассылку📬")

    chat_id = message.chat.id
    message_text = message.text

    if message_text == 'Поздравь меня🥳':
        send_file(chat_id, markup)
        return
    elif message_text == 'Ура!🎉':
        bot.send_message(chat_id, message_text, reply_markup=markup)
        return
    elif message_text == 'Подключить рассылку📬':
        pass

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


@dataclass
class Holiday():
    name: str
    href: str


def get_all_todays_holidays_links() -> List[Holiday]:
    site = SITE_WITH_POSTCARDS_HREF
    response = requests.get(site)
    if response.status_code != 200:
        print(
            f'Error while trying to get todays holidays! HTTP status code is {response.status_code}')
        return []

    hrefs = []
    today = str(datetime.today().day)
    soup = bs(response.content, "html.parser")

    for tag in soup.find_all(class_="album-info"):
        album_info = tag.find_all(class_='name')
        postcards_date = album_info[2].text
        postcards_date = postcards_date[1:postcards_date.find(' ')]
        if postcards_date == today:
            name_of_holiday = album_info[0].find('strong').text
            href = tag.find('a').get('href')
            hrefs.append(Holiday(name=name_of_holiday, href=href))
            
    return hrefs


@dataclass
class Postcard:
    holiday: str
    href: str


def get_number_of_pages(parsed_page: bs) -> int:
    soup = parsed_page.find(id='pages')
    if len(soup) == 0:
        return 1
    elif len(soup) <= 6:
        return int(soup.find_all('a')[-1].text)
    else:
        number_of_pages = soup.find_all('a')[-1].text[4:]
        return int(number_of_pages)


def get_all_todays_postcards(todays_holidays: List[Holiday]) -> List[Postcard]:
    postcards: List[Postcard] = []
    for todays_holiday in todays_holidays:
        response = requests.get(todays_holiday.href)
        if response.status_code != 200:
            print(
                f'Error while trying to get todays pictures! HTTP status code is {response.status_code}')
            return []
        soup = bs(response.content, 'html.parser')
        number_of_pages = get_number_of_pages(soup)
        for image_tag in soup.find_all('img'):
            href = image_tag.get('data-url')
            if href:
                href = href[:href.rfind('?')]
                postcards.append(
                    Postcard(holiday=todays_holiday.name, href=href))
        
        for page in range(2, number_of_pages + 1):
            response = requests.get(todays_holiday.href + f'page-{page}/')
            if response.status_code != 200:
                print(
                    f'Error while trying to get todays pictures! HTTP status code is {response.status_code}')
                return []
            soup = bs(response.content, 'html.parser')
            number_of_pages = get_number_of_pages(soup)
            for image_tag in soup.find_all('img'):
                href = image_tag.get('data-url')
                if href:
                    href = href[:href.rfind('?')]
                    postcards.append(
                        Postcard(holiday=todays_holiday.name, href=href))
    
    return postcards

def get_todays_postcards_hrefs() -> List[Postcard]:
    hrefs = get_all_todays_holidays_links()
    postcards = get_all_todays_postcards(hrefs)
    
    return postcards

def get_data() -> None:
    pass


def send_file(chat_id, markup) -> None:
    # TODO send random file
    # photo_path = get_data()
    # with open("/path/to/photo/", 'rb') as photo:
    #     bot.send_document(chat_id, photo, reply_markup=markup)
    return


def check_if_user_is_mailing(id_: int) -> bool:
    # TODO sqlite db
    return True


def start_step_handlers() -> None:
    bot.enable_save_next_step_handlers()
    bot.load_next_step_handlers()


def start_nonestop_poling() -> None:
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            sleep(5)


if __name__ == "__main__":
    Thread(target=start_step_handlers).start()

    Thread(target=start_nonestop_poling).start()
