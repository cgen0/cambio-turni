from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (ContextTypes, )

from data.keyboards import starting_keyboard
from data.states import FORCE_PROFILE, GET_NAME, SELECTING_ACTION
from log.log import Log
from utils.utils import get_channel

channel_id = get_channel()
# Enable logging
logger = Log()

async def force_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User %s in force profile. {update.message.from_user.id}")

    reply_text = (
        'Benvenuto,\nPrima di incominciare, ho bisogno del tuo nominativo.\nPer inserirlo premi sul tasto "👥 Profilo"'
    )
    markup = ReplyKeyboardMarkup([["👥 Profilo"]], one_time_keyboard=False)
    await update.message.reply_text(reply_text, reply_markup=markup)
    return FORCE_PROFILE


async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'name' in context.user_data.keys():
        reply_text = f" Il tuo nominativo é {context.user_data['name']}." \
                     f" \nSe vuoi cambiarlo, puoi inviarne uno nuovo ora." \
                     f" \nPer annullare l'operazione premi /cancel"
        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text(
            "Scrivi il tuo Nome ed il tuo Cognome", reply_markup=ReplyKeyboardRemove())

    return GET_NAME


async def save_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva il nome."""
    user = update.message.from_user
    text = update.message.text.lower().title()
    logger.info(f"Name of {user.id}: {text}")
    context.user_data["name"] = text
    markup = ReplyKeyboardMarkup(starting_keyboard, one_time_keyboard=False)
    reply_text = f" Perfetto, d'ora in poi il tuo nominativo sará {context.user_data['name']}."
    await update.message.reply_text(reply_text, reply_markup=markup)
    return SELECTING_ACTION
