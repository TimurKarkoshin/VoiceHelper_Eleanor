import json
import pyttsx3
import speech_recognition as sr
import colorama
import datetime
import sys
import webbrowser
import configparser
import nltk
import re
import requests
import psutil
import wikipedia as wiki
from fuzzywuzzy import fuzz
from os import system, path, makedirs
from random import choice
from pyowm.utils.config import get_default_config
from bs4 import BeautifulSoup
from psutil import virtual_memory as memory


with open('Intent_Data.json', 'r') as file:
    BOT_CONFIG = json.load(file)


class VoiceHelper:
    settings = configparser.ConfigParser()
    settings.read('settings.ini')

    config_dict = get_default_config()
    config_dict['language'] = 'ru'

    last_dir = ''

    def __init__(self):
        self.engine = pyttsx3.init()
        self.reco = sr.Recognizer()
        self.text = ''

        self.cmds = {
            ('добрый день', 'здравствуй'): self.hello,
            ('текущее время', 'сейчас времени', 'который час',
             'сколько времени', 'время', 'какой час'): self.time,
            ('запланируй', 'добавь задачу', 'добавь в лист задачь', 'запиши в задачи'): self.task_add,
            ('список дел', 'список задачь', 'озвучь список дел',
             'озвучь список задачь', 'дела', 'задачи'): self.task_list,
            ('загруженность', 'загруженность системы', 'нагрузка на систему',
             'какая нагрузка на систему'): self.check_memory_workload,
            ('включи музыку', 'музыка', 'подрубай музон',
             'музыку в студию', 'хочу послушать музыку', 'играй шармань'): self.music,
            ('анектод', 'расскажи анекдот', 'пошути',
             'хочу анектод', 'хохми', 'расскажи шутку'): self.joke,
            ('пока', 'до свиданья'): self.quite,
            ('выключи компьютер', 'заверши работу системы'): self.shut,
        }

        self.ndels = ['Эля', 'Элеонора', 'Элька', 'Эль', 'не могла бы ты', 'пожалуйста',
                      'текущее', 'сейчас']

        self.commands = [
            'текущее время', 'сейчас времени', 'который час', 'сколько времени', 'время', 'какой час',
            'открой браузер', 'запусти браузер', 'браузер',
            'добрый день', 'здравствуй',
            'запланируй', 'добавь задачу', 'добавь в лист задачь', 'запиши в задачи',
            'список дел', 'список задачь', 'озвучь список дел', 'озвучь список задачь', 'дела', 'задачи',
            'загруженность', 'загруженность системы', 'нагрузка на систему', 'какая нагрузка на систему',
            'пока', 'до свиданья',
            'выключи компьютер'
        ]

        self.num_task = 0
        self.j = 0
        self.ans = ''
        wiki.set_lang('ru')

    def cleaner(self, text):
        """
        Очистка текста
        :param text:
        :return:
        """

        self.text = text

        for i in self.ndels:
            self.text = self.text.replace(i, '').strip()
            self.text = self.text.replace('  ', ' ').strip()

        self.ans = self.text

        for i in range(len(self.commands)):
            k = fuzz.ratio(text, self.commands[i])
            if (k > 70) & (k > self.j):
                self.ans = self.commands[i]
                self.j = k

        return str(self.ans)

    def check_memory_workload(self):
        """
        Проверка загруженности памяти компьютера
        :return:
        """
        memory_check = memory()
        self.talk(f'Загруженность памяти компьютера составляет {round(memory_check.percent)}%')

    def check_disk_worload(self):
        """
        Проверка загруженности диска
        :return:
        """
        total, used, free, percent = psutil.disk_usage('C:/')

        self.talk(f'Общее простратсво диска {total // (2 **30)}, '
                  f'из них {used// (2 **30)} гигабайт занято, {free// (2 **30)} свободно.'
                  f'Значит диск занят на {percent} процентов')

    def create_folder(self, task):
        """
        Создаёт папку
        :param task:
        :return:
        """
        words = ['Создай папку', 'Сделай папку', 'Смастери папку', 'Создай папку с именем', 'Сделай папку с именем']

        for i in words:
            task = task.replace(i, '').replace('  ', ' ').strip()

        if not path.exists(task):
            makedirs(task)
            self.talk(f'Папка с именем {task} была успешно создана')
            VoiceHelper.last_dir = task
        else:
            self.talk(f'Папка с именем {task} уже существует')

    def create_file_in_folder(self, task):
        """
        Создаёт файл в папке(из функции create_folder)
        :param task:
        :return:
        """
        words = ['Создай файл', 'Сделай файл', 'Смастери файл', 'Создай файл с именем', 'Сделай файл с именем']

        if VoiceHelper.last_dir == '':
            self.talk('Перед созданием файла необходимо создать папку. '
                      'Вы можете сделать это с помощью голосовой команды "Создай папку"')

        for i in words:
            task = task.replace(i, '').replace('  ', ' ').strip()

        tasks = task.split()

        for i in tasks:
            if fuzz.ratio(i, 'проект') > 70:
                with open(f"{VoiceHelper.last_dir}/main.py", "w") as file:
                    file.write("""Пример""")

                    self.talk('Файл создал успешно')

        if not path.exists((f"{VoiceHelper.last_dir}/{task}")):
            if "." not in task:
                task += ".txt"

            with open((f"{VoiceHelper.last_dir}/{task}"), 'w') as file:
                file.write('')

            self.talk(f"Файл с именем {task} успешно создан")
        else:
            self.talk(f"Файл с именем {task} уже существует")

    def intent_cleaner(self, text):
        """
        Очищает интенты
        :param text:
        :return:
        """
        cleaned_text = ''
        for i in text.lower():
            if i in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz':
                cleaned_text += i
        return cleaned_text

    def match(self, text, example):
        """
        Конвертация текста библеотекой nltk
        :param text:
        :param example:
        :return:
        """
        return nltk.edit_distance(text, example) / len(example) < 0.4 if len(example) > 0 else False

    def get_intent(self, text):
        """
        Выгрузка интентов из файла
        :param text:
        :return:
        """
        for intent in BOT_CONFIG['intents']:
            if 'examples' in BOT_CONFIG['intents'][intent]:
                for example in BOT_CONFIG['intents'][intent]['examples']:
                    if self.match(self.intent_cleaner(text), self.intent_cleaner(example)):
                        return intent

    def intenter(self, text):
        """
        Сопоставление интентов и поддерживаемых команд
        :param text:
        :return:
        """
        intent = self.get_intent(text)

        if intent is None:
            return

        self.talk(choice(BOT_CONFIG['intents'][intent]['responses']))

    def task_add(self):
        """
        Добавление команды в список
        :return:
        """
        self.talk('Какую задачу добавить в список?')
        task = self.listen()

        with open('Task_List.txt', 'a') as file:
            file.write(f'{task}\n')

        self.talk(f'Задача {task} успешно добавлена в список')

    def task_list(self):
        """
        Вывод списка задач
        :return:
        """
        with open('Task_List.txt', 'r') as file:
            tasks = file.read()

        self.talk(f'Список задач: {tasks}')

    def web_search(self, search):
        """
        Поиск в браузере
        :param search:
        :return:
        """
        words = [
            'найди', 'найти',
            'поищи', 'поиск',
            'ищи', 'искать'
        ]
        remove = [
            'пожалуйста', 'быстро',
            'давай', 'ладно'
        ]

        for i in words:
            search = search.replace(i, '')
            for j in remove:
                search = search.replace(j, '').strip()

        self.talk(f'Выполняю поисковой запрос {search}')

        webbrowser.open(f'https://yandex.ru/search/?text={search}'
                        f'&clid=2270455&banerid=6301000000%3A637a82f266dcc743722cc869&win=568&lr=35')
        self.search_wiki(search)

    def recognizer(self):
        """
        Рекогнайзер, передаёт данные для интерпритации интентов
        :return:
        """
        self.text = self.cleaner(self.listen())
        print(self.text)

        if self.text.startswith(('открой', 'запусти', 'зайди на', 'зайди на сайт')):
            self.opener(self.text)

        elif self.text.startswith(('найди на карте', 'найти на карте', 'поищи на карте',
                                   'поиск на карте', 'ищи на карте', 'искать на карте')):
            self.map_searching(self.text)

        elif self.text.startswith(('найди', 'найти', 'поищи', 'поиск', 'ищи', 'искать')):
            self.web_search(self.text)

        elif self.text.startswith(('переведи', 'перевести', 'перевод', 'переводить')):
            self.translate(self.text)

        for tasks in self.cmds:
            for task in tasks:
                if fuzz.ratio(task, self.text) >= 80:
                    self.cmds[tasks]()
                    return

        self.intenter(self.text)

    def give_facts(self):
        """
        Выдаёт случайный факт
        :return:
        """
        url = 'https://randstuff.ru/fact/'
        responce = requests.get(url)

        soup = BeautifulSoup(responce.content, 'html.parser').findAll('td')
        item = list(soup)
        fact = item[0]

        self.talk(str(fact).replace('<td>', '').replace('</td>', '').replace('  ', '  '))

    def time(self):
        """
        Считывает регион и озвучивает местное время
        :return:
        """
        self.talk("Уточняю время в регионе вашей системы")
        now = datetime.datetime.now()
        self.talk("Сейчас " + str(now.hour) + ":" + str(now.minute))

    def music(self):
        """
        Включает случайную музыку из плейлиста
        :return:
        """
        self.talk(choice(['Включаю музыку',
                          'Вдарим рок в этой дыре',
                          'Устанавливаю контакт с вашими ушками посредством музыкального воздействия'])
                  )
        music_playlist = [
            'https://www.youtube.com/watch?v=scW0ReWzIJU&t=1s', 'https://www.youtube.com/watch?v=0-C0lCPFTj8&t=234s',
            'https://www.youtube.com/watch?v=R8j9qmVJ1JA', 'https://www.youtube.com/watch?v=eLztDVkV6G0',
            'https://www.youtube.com/watch?v=Jm-7DODaTvU', 'https://www.youtube.com/watch?v=gnqXfK-ESoY'
        ]
        webbrowser.open(choice(music_playlist))

    def translate(self, task):
        """
        Переводит озвученный текст
        :param task:
        :return:
        """
        self.talk(choice(["Осуществляю перевод", "Перевожу текст", "Выполняю перевод"]))
        variants = [
            'переведи', 'перевод', 'переведи текст',
            'перевод текста', 'какой перевод', 'сделай перевод'
        ]

        for i in variants:
            task = task.replace(i, "").replace("  ", " ").strip()

        webbrowser.open(f"https://translate.yandex.ru/?source_lang=en&target_lang=ru&text={task}")

    def map_searching(self, task):
        """
        Поиск по озвученному обьекту на картах google
        :param task:
        :return:
        """
        for j in ("найди на карте", "поиск на карте", "покажи место", "открой на карте"):
            task = task.replace(j, '').replace('  ', ' ').strip()

            for i in ["находится", "расположен", "где"]:
                for k in ["мне", "нам", "им", "всем"]:
                    if fuzz.ratio(task.split()[0], i) > 70 or fuzz.ratio(task.split()[0], k) > 70:
                        task = " ".join(task.split()[1:])
                    task = task.replace(i, "").replace(k, "").replace("  ", " ").strip()
        webbrowser.open(f"https://www.google.ru/maps/search/{task}")
        self.talk(f"Выполняю поиск в Google maps по запросу {task}")

    def search_wiki(self, task):
        """
        Поиск страницы wikipedia
        :param task:
        :return:
        """
        try:
            info = wiki.summary(task, sentences=3)
            self.talk((info.replace('англ', '')).replace('род.', 'родился').replace('(.', '').replace(')', '')
                      .replace(';', '').replace("(урожд. —", "").replace("урожд.", "").replace("  ", " "))
        except wiki.exceptions.PageError:
            pass
        except wiki.exceptions.WikipediaException:
            pass

    def joke(self):
        """
        Выдаёт случайную шутку с сайта анекдотов
        :return:
        """
        link = requests.get("https://www.anekdot.ru/random/anekdot/")
        parser = BeautifulSoup(link.text, "html.parser")
        select = parser.select(".text")
        get = (select[0].getText().strip())
        regular = re.compile("[^a-zA-Zа-яА-я ^0-9:.,!?-]")
        joke = regular.sub("", get)
        self.talk(joke)

    def opener(self, task):
        """
        Открывает на выбор имеющийся в списке сервис
        :param task:
        :return:
        """
        links = {
            ('youtube', 'ютуб', 'ютюб'): 'https://youtube.com/',
            ('вк', 'вконтакте', 'контакт', 'vk'): 'https:vk.com/feed',
            ('браузер', 'интернет', 'browser'): 'https://ya.ru/',
            ('gmail', 'гмейл', 'гмеил', 'гмаил'): 'https://mail.google.com/',
            ('yandex', 'яндекс', 'яндикс',): 'https://mail.yandex.ru/',
        }
        j = 0
        if 'и' in task:
            task = task.replace('и', '').replace('  ', ' ')
        double_task = task.split()
        if j != len(double_task):
            for i in range(len(double_task)):
                for vals in links:
                    for word in vals:
                        if fuzz.ratio(word, double_task[i]) > 75:
                            webbrowser.open(links[vals])
                            self.talk('Открываю ' + double_task[i])
                            j += 1
                            break

    def cfile(self):
        """
        Функция - настройка
        :return:
        """
        try:
            cfr = VoiceHelper.settings['SETTINGS']['fr']
            if cfr != 1:
                file = open('settings.ini', 'w', encoding='UTF-8')
                file.write('[SETTINGS]\ncountry = RU\nplace = Krasnodar\nfr = 1')
                file.close()
        except Exception as e:
            print('Сбой работы: Необходим перезапуск программы!', e)
            file = open('settings.ini', 'w', encoding='UTF-8')
            file.write('[SETTINGS]\ncountry = RU\nplace = Krasnodar\nfr = 1')
            file.close()

    def quite(self):
        """
        Завершения работы бота
        :return:
        """
        self.talk(choice(['Доброго вам дня', 'Работа выполнена!', 'Пока пока']))
        self.engine.stop()
        system('cls')
        sys.exit(0)

    def shut(self):
        """
        Завершения работы системы
        :return:
        """
        self.talk("Подтвердите действие!")
        text = self.listen()
        print(text)
        if (fuzz.ratio(text, 'подтвердить') > 60) or (fuzz.ratio(text, "подтверждаю") > 60):
            self.talk('Действие подтверждено')
            self.talk('До скорых встреч!')
            system('shutdown /s /f /t 10')
            self.quite()
        elif fuzz.ratio(text, 'отмена') > 60:
            self.talk("Действие не подтверждено")
        else:
            self.talk("Действие не подтверждено")

    def hello(self):
        """
        Приветствие
        :return:
        """
        self.talk(choice(['Добрый день', 'Здравствуй']))

    def talk(self, text):
        """
        Воспроизведение речи
        :param text:
        :return:
        """
        print(text)
        self.engine.say(text)
        self.engine.runAndWait()
        self.engine.stop()

    def listen(self):
        """
        Прослушка
        :return:
        """
        with sr.Microphone() as source:
            print(colorama.Fore.GREEN + "Ожидаю команды!")
            self.reco.adjust_for_ambient_noise(source)
            audio = self.reco.listen(source)
            try:
                self.text = self.reco.recognize_google(audio, language="ru-RU").lower()
            except Exception as e:
                print(e)
            return self.text


VoiceHelper().cfile()

while True:
    try:
        VoiceHelper().recognizer()
    except Exception as ex:
        print(ex)
