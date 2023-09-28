import traceback

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (ContextTypes, ConversationHandler)

from data.keyboards import starting_keyboard
from data.states import SELECTING_ACTION, FORCE_PROFILE
from log.log import Log
from utils.utils import get_control_id

# Enable logging
logger = Log()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Avvia la conversazione (solo se l'utente appartiene al gruppo di controllo). Chiede all'utente di inserire il suo nome se non l'ha giá fatto. """
    group_id = get_control_id()
    chat_member = await context.bot.get_chat_member(user_id=update.message.from_user.id, chat_id=int(group_id))
    if not chat_member.status in ['creator', 'administrator', 'member'] or  update.message.chat.type != "private":
        print("not a member")
        return ConversationHandler.END
    context.user_data.pop("new_announce", None)
    if 'name' in context.user_data.keys():
        reply_text = (
            f" Bentornato {context.user_data['name']}"
        )
        markup = ReplyKeyboardMarkup(starting_keyboard, one_time_keyboard=False)
        await update.message.reply_text(reply_text, reply_markup=markup)
        return SELECTING_ACTION

    else:
        reply_text = (
            'Benvenuto,\nPrima di incominciare, ho bisogno del tuo nominativo.\nPer inserirlo premi sul tasto "👥 Profilo"'
        )
        markup = ReplyKeyboardMarkup([["👥 Profilo"]], one_time_keyboard=False)
        await update.message.reply_text(reply_text, reply_markup=markup)
        return FORCE_PROFILE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info(f'''User {user.first_name if user.first_name is not None else user.id} canceled the operation.''')

    """Removing unfinished announce insertion"""
    context.user_data.pop("new_announce", None)

    if 'name' in context.user_data.keys():
        markup = ReplyKeyboardMarkup(starting_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Operazione annullata.", reply_markup=markup
        )
        return SELECTING_ACTION
    else:
        markup = ReplyKeyboardMarkup([["👥 Profilo"]], one_time_keyboard=False)
        await update.message.reply_text("Operazione annullata.", reply_markup=markup)
        return FORCE_PROFILE


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.info(f"Exception while handling an update:{tb_string}")
