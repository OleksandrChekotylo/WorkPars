import json
import requests
import sqlite3
import telebot
import time
import random
import bs4


class SQLite:
    def __init__(self, file='work.db'):
        self.file = file

    def __enter__(self):
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()


def update_database(vacancy_info_list: list, db_name: str):
    bot = telebot.TeleBot('TOKEN')
    ban_words = ['support', 'підтримк', 'перекладач', 'поддержк', 'підримк', 'продаж', 'дизайнер', 'designer',
                 'manager',
                 'менедж', 'викладач', 'assistant', 'копирайтер', 'sale', 'мова', 'язык', 'копірайтер', 'арбитражник',
                 'маркет', '3D', 'аналітик', 'юрист', 'таргет', 'таргет', 'контент,', 'SEO', 'школ', 'supp',
                 'salesforce']
    try:
        with SQLite(r'work.db') as cur:
            id_list = [vacancy[0] for vacancy in cur.execute(f"""SELECT id FROM {db_name} """)]
            for vacancy in vacancy_info_list:
                if vacancy.get('id') in id_list:
                    continue
                name = vacancy.get('name').lower()
                if len(list([1 for ban_word in ban_words if ban_word in name])):
                    continue
                cur.execute(f"""INSERT INTO {db_name} VALUES (?,?,?)""", [
                    int(vacancy.get('id')), vacancy.get('name'), vacancy.get('url')])
                bot.send_message(chat_id='user id',
                                 text=vacancy.get('url') + "\n\n" + vacancy.get('name') + '\n', parse_mode='')
    except sqlite3.OperationalError as ex1:
        print('database update error',ex1)


def search_vacancy_robota_ua():
    vacancy_info_list = []
    rabota_ua_vacancy_data = {}
    url = 'https://api.rabota.ua/vacancy/search?count=30&parentId=1&scheduleId=3&profLevelIds=2'
    try:
        r = requests.get(url)
        rabota_ua_vacancy_data = json.loads(r.content).get('documents')
    except TypeError or AttributeError:
        print('rabota_ua request error')
    try:
        for vacancy in rabota_ua_vacancy_data:
            vacancy.update({'url': 'https://rabota.ua/ua/company12702464/vacancy' + str(vacancy.get('id'))})
            vacancy_info_list += [vacancy]
    except TypeError or AttributeError:
        print('rabota_ua_error')
    if vacancy_info_list:
        update_database(vacancy_info_list, 'robota_ua')


def work_ua_parser(text, tag):
    html_text = bs4.BeautifulSoup(text.text, 'html.parser')
    vacancy_info_list = []
    for vacancy_card in html_text.find_all('div', class_=tag):
        vacancy_name = vacancy_card.find('h2')
        vacancy_href = vacancy_card.find(href=True)
        try:
            vacancy_info_list += [{
                'id': int(vacancy_href['href'][6:-1]),
                'name': vacancy_name.text[1:-1],
                'url': 'www.work.ua' + vacancy_href['href']
            }]
        except TypeError or AttributeError:
            print('work_ua dict error')
    return vacancy_info_list


def search_vacancy_work_ua():
    r = ''
    for page in range(1, 5):
        url = 'https://www.work.ua/jobs-remote-it/?advs=1&experience=1&page=' + str(page)
        try:
            r = requests.get(url)
        except TypeError or AttributeError:
            print('work_ua request error')
        vacancy_info_list = work_ua_parser(r, 'card card-hover card-visited wordwrap job-link')
        vacancy_info_list += work_ua_parser(r, 'card card-hover card-visited wordwrap job-link js-hot-block')
        if vacancy_info_list:
            update_database(vacancy_info_list, 'work_ua')
        time.sleep(5)


def search_vacancy_dou_ua():
    url = 'https://jobs.dou.ua/vacancies/?remote&exp=0-1'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/50.0.2661.102 Safari/537.36'}
    r = ''
    try:
        r = requests.get(url, headers=headers).text
    except TypeError or AttributeError:
        print('dou_ua request error')
    html_text = bs4.BeautifulSoup(r, 'html.parser')
    vacancy_info_list = []
    for vacancy in html_text.find_all('li', 'l-vacancy'):
        try:
            vacancy_info_list += [{
                'name': vacancy.find('a', class_='vt').text,
                'id': int(vacancy.find('div', class_='vacancy').attrs.get('_id')),
                'url': vacancy.find('a', class_='vt', href=True)['href']}]
        except TypeError or AttributeError:
            print('dou_ua dict error')
    if vacancy_info_list:
        update_database(vacancy_info_list, 'dou_ua')


def search_vacancy_djinni_ua():
    url = 'https://djinni.co/jobs/?exp_level=no_exp'
    r = ''
    try:
        r = requests.get(url).text
    except TypeError or AttributeError:
        print('work_ua request error')
    html_text = bs4.BeautifulSoup(r, 'html.parser')
    vacancy_info_list = []
    for vacancy in html_text.find_all('li', class_='list-jobs__item'):
        try:
            vacancy_info_list += [{
                'name': vacancy.find('span').text,
                'url': 'https://djinni.co' + vacancy.find('a', class_='profile', href=True)['href'],
                'id': int(vacancy.find('a', class_='profile', href=True)['href'][6:11])
            }]
        except TypeError or AttributeError:
            print('djinni_ua dict error')
    if vacancy_info_list:
        update_database(vacancy_info_list, 'djinni_ua')


try:
    while True:
        print(time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime()))
        search_vacancy_robota_ua()
        search_vacancy_djinni_ua()
        search_vacancy_work_ua()
        search_vacancy_dou_ua()
        time.sleep(random.randint(500, 600))
except Exception as ex:
    print(ex)
