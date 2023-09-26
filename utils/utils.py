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
    """Sets current year to parsed date if day and month are bigger than today's,
     otherwise sets year as next year. Returns None if string is not correctly formatted"""
    try:
        date = datetime.strptime(date_text, '%d/%m')
        today = datetime.now()
        t = datetime(day=today.day, month=today.month, year=1900)
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
