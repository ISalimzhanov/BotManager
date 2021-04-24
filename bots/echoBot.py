from threading import Thread

import requests
import telebot
from telebot.types import *


class EchoBot:
    def __init__(self, token: str):
        self.__tg_api = telebot.TeleBot(token)
        self.__token = token

    def echo_all(self, message: Message):
        self.__tg_api.send_message(message, message.text)

    def update(self):
        while True:
            try:
                self.__tg_api.polling(none_stop=True)
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ProxyError,
                    requests.exceptions.ConnectionError):
                continue

    def run(self) -> Thread:
        @self.__tg_api.message_handlers(content_types=['text'])
        def response(message: Message):
            self.echo_all(message)
        thread = Thread(target=self.update)
        print(f"Bot with token {self.__token} is launched")
        return thread
