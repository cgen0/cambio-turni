import os
from datetime import datetime


def get_token():
    """Reads token from config file"""
    try:
        return os.environ['TOKEN']
    except KeyError:
        return None


def get_aws_credentials():
    """Reads aws token from config file"""
    try:
        return os.environ['ACCESS_KEY_ID'], os.environ['SECRET_ACCESS_KEY'], os.environ['AWS_REGION']
    except KeyError:
        return None


def get_control_id():
    """Reads token from config file"""
    try:
        return os.environ['CONTROL_GROUP_ID']
    except KeyError:
        return None


def get_channel():
    """Reads channelId from config file"""
    try:
        return os.environ['CHANNEL_ID']
    except KeyError:
        return None


def validate_date_and_guess_year(date_text):
    """Sets the current year to the parsed date if the day and month are later than today's;
    otherwise, sets the year to the next year. Returns None if the string is not correctly formatted.

    Note: Appending a leap year ("1904") to the date string prevents a ValueError for date_text=="29/02".
    """
    # Appending a leap year ("1904") to the date string
    date_text += "/1904"
    try:
        date = datetime.strptime(date_text, '%d/%m/%Y')
        today = datetime.now()
        # 1904 is a leap year unlike 1900, so it does not throw a ValueError if today is 29/02.
        t = datetime(day=today.day, month=today.month, year=1904)
        if date < t:
            date = datetime(day=date.day, month=date.month, year=today.year + 1)
        else:
            date = datetime(day=date.day, month=date.month, year=today.year)

        return date.strftime("%d-%m-%Y")
    except ValueError:
        return None


def is_time_valid(time_text):
    """Checks if time_text is correctly formatted"""
    try:
        s, e = time_text.replace(" ", "").split("-")
        a = datetime.strptime(s, '%H:%M')
        b = datetime.strptime(e, '%H:%M')

        return True
    except ValueError:
        return False
