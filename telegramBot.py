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
from pathlib import Path
from pytube import YouTube
from random import choice, randint
from telebot.apihelper import ApiTelegramException
import schedule
from exceptions import *
import sqlite3
import logging

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
    logging.info(f"start message send to a '{message.from_user.full_name}' whose id is = '{message.from_user.id}'")


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
        
    elif message_text == 'Ура!🎉':
        bot.send_message(chat_id, message_text, reply_markup=markup)
        
    elif message_text == 'Подключить рассылку📬':
        markup = customize_markup(
            "Поздравь меня🥳", "Ура!🎉", "Отключить рассылку📬")
        if user_is_mailing:
            bot.send_message(message.from_user.id, 'Ты уже подключил рассылку, шизофреник', reply_markup=markup)
        else:
            msg = bot.send_message(message.from_user.id, "Во сколько хотите получать рассылку? (Например: 07:00)", reply_markup=markup)
            bot.register_next_step_handler(msg, mailing_time_setup)
            
    elif message_text == 'Отключить рассылку📬':
        markup = customize_markup(
            "Поздравь меня🥳", "Ура!🎉", "Подключить рассылку📬")
        if not user_is_mailing:
            bot.send_message(message.from_user.id, 'У тебя ее и так нет, лох', reply_markup=markup)
        else:
            remove_user_from_mailing(message.from_user.id)
            bot.send_message(message.from_user.id, 'Рассылка отключена😈', reply_markup=markup)
    
    logging.info(f"'{message.from_user.full_name}' whose id = '{user_id}' send message: '{message_text}'")
    
def mailing_time_setup(message: Message) -> None:
    markup = customize_markup(
            "Поздравь меня🥳", "Ура!🎉", "Отключить рассылку📬")
    msg = message.text
    if msg in BUTTONS:
        main(message=message)
        return
    try:
        small_version = str( int( msg.replace(':', '') ) )
        msg_legth = len(small_version)
        if msg_legth < 3 or msg_legth > 5:
            raise ImpossibleTime
        if msg_legth == 3:
            msg = '0' + small_version[0] + ':' + small_version[1:]
        if int(msg[3:])>60 or int(msg[3:])<0 or int(msg[:2])>=24 or int(msg[:2])<0:
            raise ImpossibleTime
    except (ValueError, ImpossibleTime):
        bot.send_message(message.from_user.id, f'Твое iq равно {str(randint(30, 60))}', reply_markup=markup)
    else:
        bot.send_message(message.from_user.id, f'Рассылка в {msg} успешно подключена🤙🤣🤣', reply_markup=markup)
        add_user_to_mailing(message.from_user.id, message.chat.id, msg)
        
def remove_user_from_mailing(id_: int) -> None:
    con = sqlite3.connect('instance/mailing.sqlite3')
    cursor = con.cursor()
    cursor.execute(f"""
                   DELETE FROM mailing_users WHERE user_id={id_}
                   """)
    con.commit()
    con.close()
    
    logging.info(f"User {id_} unsubscribed from mailing")
        
def add_user_to_mailing(users_id: int, chat_id: int, time: str) -> None:
    con = sqlite3.connect('instance/mailing.sqlite3')
    cursor = con.cursor()
    cursor.execute(f"""
                   INSERT INTO mailing_users (user_id, chat_id, time)
                   VALUES ({users_id}, {chat_id}, "{time}")
                   """)
    
    con.commit()
    con.close()
    
    logging.info(f"User {users_id} subscribed for mailing")


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
        logging.error(
            f'Error while trying to get todays holidays! HTTP status code is {response.status_code}')
        raise NoResponseFromTheSite(f"HTTP status code = {response.status_code}")

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

    logging.info("Todays holidays hrefs were successfully downloaded")
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
    number_of_pages = 1
    
    def youtube_href_to_download_href(youtube_href: str) -> str:
        yt = YouTube(youtube_href)
        stream = yt.streams.get_highest_resolution()
        download_url = stream.url
        return download_url

    def get_if_it_is_youtube_href(href: str) -> bool:
        for i in range(len(href)):
            if href[-i] == '.':
                return False
            elif href[-i] == '/':
                return True

    def get_picture_href_from_its_page(page_href: str) -> str:
        response = requests.get(page_href)
        if response.status_code != 200:
            logging.error(
                f'Error while trying to get picture through its own page! HTTP status code is {response.status_code}')
            raise NoResponseFromPicturesPage(f"HTTP status code = {response.status_code}")
        soup = bs(response.content, 'html.parser')
        button = soup.find(id='download-card-button')
        href = button.get('href')
        if get_if_it_is_youtube_href(href):
            href = youtube_href_to_download_href(href)
        return href

    def get_postcards_hrefs_from_page(todays_holiday: Holiday, first_use: bool = False, page: int = 0) -> List[Postcard]:
        postcards: List[Postcard] = []
        if page:
            response = requests.get(todays_holiday.href + f'page-{page}/')
        else:
            response = requests.get(todays_holiday.href)
        if response.status_code != 200:
            logging.error(
                f'Error while trying to get todays pictures! HTTP status code is {response.status_code}')
            raise NoResponseFromTheHolidaysPage(f"HTTP status code = {response.status_code}")
        soup = bs(response.content, 'html.parser')
        if first_use:
            nonlocal number_of_pages
            number_of_pages = get_number_of_pages(soup)
        for card in soup.find_all(class_='card'):
            pictures_page = card.find('a').get('href')
            href = get_picture_href_from_its_page(pictures_page)
            postcard = Postcard(holiday=todays_holiday.name, href=href)
            postcards.append(postcard)

        return postcards

    for todays_holiday in todays_holidays:
        postcards: List[Postcard] = get_postcards_hrefs_from_page(
            todays_holiday=todays_holiday, first_use=True)
        for page in range(2, number_of_pages + 1):
            postcards.extend(get_postcards_hrefs_from_page(
                todays_holiday=todays_holiday, page=page))

    return postcards


def get_todays_postcards_hrefs() -> List[Postcard]:
    hrefs = get_all_todays_holidays_links()
    postcards = get_all_todays_postcards(hrefs)
    return postcards


def download_postcard_to_cache_folder(file_url: str) -> None:
    response = requests.get(file_url)
    if response.status_code != 200:
        logging.error(
            f'Error while downloading a picture! Http status code: {response.status_code}')
        raise NoResponseFromPicturesDownloadHref(f"HTTP status code = {response.status_code}")
    image = response.content
    if file_url[-4] != '.':
        addition = '.mp4'
    else:
        addition = file_url[-4:]
    filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f") + addition
    current_path = Path(__file__).parent.resolve()
    path_to_file = current_path / "cache" / filename
    with open(path_to_file, 'wb') as f:
        f.write(image)
        
    logging.info("Postcard was successfully downloaded")


def download_all_postcards(todays_postcards: List[Postcard]) -> None:
    for postcard in todays_postcards:
        download_postcard_to_cache_folder(postcard.href)
        
def clear_postcards() -> None:
    
    for filename in os.listdir('cache'):
        os.remove('cache/' + filename)
    
    logging.info("Postcards were successfully deleted")


def download_todays_postcards() -> None:
    clear_postcards()
    todays_holidays_hrefs = get_all_todays_holidays_links()
    todays_postcards_hrefs = get_all_todays_postcards(todays_holidays_hrefs)
    download_all_postcards(todays_postcards_hrefs)

    logging.info("Postcards were successfully downloaded!")
    
def get_random_picture() -> str:
    if not os.listdir('cache/'):
        logging.info("There is no holidays today :(")
        raise NoPictureAvailable("There is no holidays today :(")
    return choice([filename for filename in os.listdir('cache/')])

def check_if_video(path: Path) -> bool:
    format_ = path.suffix
    return format_ in VIDEO_FORMATS

def send_file(chat_id, markup) -> None:
    try:
        filename = get_random_picture()
    except NoPictureAvailable:
        bot.send_message(chat_id, 'Сегодня нет праздников :(', reply_markup=markup)
    else:
        photo_path = Path(__file__).parent / "cache" / filename
        video = check_if_video(photo_path)
        if video:
            with open(photo_path, 'rb') as video:
                bot.send_video(chat_id, video, reply_markup=markup)
        else:
            try:
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, reply_markup=markup)
            except ApiTelegramException:
                photo_path.unlink()
                send_file(chat_id, markup)
            
def create_db() -> None:
    os.mkdir('instance')
    con = sqlite3.connect('instance/mailing.sqlite3')
    cursor = con.cursor()
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS mailing_users (
                    user_id INTEGER UNIQUE NOT NULL,
                    chat_id INTEFER UNIQUE NOT NULL,
                    time TEXT NOT NULL
                )
                """)
    con.commit()
    con.close()
    
    logging.info("mailing_users database were successfully created")

# Downloading and checking mailing
def start_schedule_tasks() -> None:
    if not os.path.exists('instance'):
        create_db()
    if not os.path.exists('cache'):
        os.mkdir('cache')
        download_todays_postcards()
    elif len(os.listdir('cache')) == 0:
        download_todays_postcards()
    schedule.every().day.at("00:10").do(download_todays_postcards)
    schedule.every().minute.do(start_mailing)
    logging.info("schedule tasks were started")
    while True:
        schedule.run_pending()

def start_mailing() -> None:
    current_time = datetime.today().strftime("%H:%M")
    con = sqlite3.connect('instance/mailing.sqlite3')
    cursor = con.cursor()
    cursor.execute(f"""
                   SELECT * FROM mailing_users
                   """)
    row = cursor.fetchall()
    con.close()
    
    for user_id, chat_id, time in row:
        markup = customize_markup(
            "Поздравь меня🥳", "Ура!🎉", "Отключить рассылку📬")
        if time == current_time:
            send_file(chat_id=chat_id, markup=markup)
    

def check_if_user_is_mailing(id_: int=0) -> bool:
    con = sqlite3.connect('instance/mailing.sqlite3')
    cursor = con.cursor()
    cursor.execute(f"""
                   SELECT * FROM mailing_users WHERE user_id={id_}
                   """)
    row = cursor.fetchone()
    con.close()
    
    return row is not None


def setup_step_handlers() -> None:
    bot.enable_save_next_step_handlers()
    bot.load_next_step_handlers()


def start_nonestop_poling() -> None:
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            sleep(5)

def setup_logging() -> None:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    logging.basicConfig(level=logging.INFO, filename='logs/logs.log',
                        format='%(asctime)s %(levelname)s %(message)s', encoding='UTF-8')

if __name__ == "__main__":
    setup_logging()
    setup_step_handlers()
    Thread(target=start_schedule_tasks).start()
    Thread(target=start_nonestop_poling).start()