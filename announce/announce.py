import locale
from datetime import datetime, timedelta

from telegram.helpers import escape_markdown

locale.setlocale(locale.LC_ALL, 'it_IT.utf8')


class Announce:

    def __init__(self, announce):
        self.user_id = announce["user_id"]
        self.user_name = announce["user_name"]
        self.type = announce["type"]
        self.category = announce["category"]

        if isinstance(announce["date_start"], int):
            self.date_start = announce["date_start"]
            self.date_end = announce["date_end"]
        else:
            date_start_string = f"""{announce["date_start"]}-{announce["time_start"]}"""
            date_end_string = f"""{announce["date_start"]}-{announce["time_end"]}"""

            self.date_start = int(datetime.strptime(date_start_string, "%d-%m-%Y-%H:%M").timestamp())
            if self.category == "RFD":
                self.date_end = int(
                    (datetime.strptime(date_end_string, "%d-%m-%Y-%H:%M") + timedelta(days=1)).timestamp())
            else:
                self.date_end = int(datetime.strptime(date_end_string, "%d-%m-%Y-%H:%M").timestamp())
                if self.date_end < self.date_start:
                    self.date_end = int(
                        (datetime.strptime(date_end_string, "%d-%m-%Y-%H:%M") + timedelta(days=1)).timestamp())

        self.info = announce["info"]
        self.message_id = announce["message_id"]

    def to_message(self, username=None):
        if username:
            username = escape_markdown(username, version=2)
            username = f"""\(@{username}\)"""
            name = escape_markdown(self.user_name, version=2)
        else:
            name = f"""[{self.user_name}](tg://user?id={self.user_id})"""
            username = ""

        if self.category == "RFD":
            if self.type == "Cedo":
                string = (f"""Inizio: {datetime.fromtimestamp(self.date_start).strftime("%d %B %H:%M").title()}\n"""
                          f"""Fine: {datetime.fromtimestamp(self.date_end).strftime("%d %B %H:%M").title()}\n"""
                          f"""{self.type} {self.category}\n"""
                          f"""Info Aggiuntive: {self.info}""")
            else:
                string = (f"""Inizio: {datetime.fromtimestamp(self.date_start).strftime("%d %B").title()}\n"""
                          f"""Fine: {datetime.fromtimestamp(self.date_end).strftime("%d %B").title()}\n"""
                          f"""{self.type} {self.category}\n"""
                          f"""Info Aggiuntive: {self.info}""")

        elif self.category == "Riposo":
            string = (f"""Data: {datetime.fromtimestamp(self.date_start).strftime("%d %B").title()}\n"""
                      f"""{self.type} {self.category}\n"""
                      f"""Info Aggiuntive: {self.info}""")

        elif self.category == "Stecca":
            string = (
                f"""Data: {datetime.fromtimestamp(self.date_start).strftime("%d %B").title()} - {datetime.fromtimestamp(self.date_end).strftime("%d %B").title()}\n"""
                f"""{self.type} {self.category}\n"""
                f"""Info Aggiuntive: {self.info}""")
        elif self.category == "Ferie":
            string = (f"""{self.type} {self.category}\n"""
                      f"""Info Aggiuntive: {self.info}""")
        else:
            string = (f"""Data: {datetime.fromtimestamp(self.date_start).strftime("%d %B").title()}\n"""
                      f"""Orario: {datetime.fromtimestamp(self.date_start).strftime("%H:%M")} - """
                      f"""{datetime.fromtimestamp(self.date_end).strftime("%H:%M")}\n"""
                      f"""{self.type} {self.category}\n"""
                      f"""Info Aggiuntive: {self.info}""")
        string = f"""Da: {name} {username}\n""" + escape_markdown(string, version=2)
        return string

    def __str__(self):
        return self.to_message()

    def __iter__(self):
        """Makes Announce castable to tuple"""

        yield self.user_id
        yield self.user_name
        yield self.type
        yield self.category
        yield self.date_start
        yield self.date_end
        yield self.info
        yield self.message_id

    @staticmethod
    def announce_from_rows(data_list):
        pass
