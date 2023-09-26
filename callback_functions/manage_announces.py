from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (ContextTypes, )

from data.states import SELECTING_ACTION
from database.database import Database
from log.log import Log
from utils.utils import get_channel

channel_id = get_channel()

# Enable logging
logger = Log()


async def get_announces(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ottieni tutti gli annunci inseriti dall'utente"""
    user_id = update.message.from_user.id
    with Database() as db:
        announces = db.get_user_announces(user_id)

    if len(announces) == 0:
        await context.bot.send_message(chat_id=user_id, text="Non ci sono tuoi annunci sul canale al momento")

    for a in announces:
        await context.bot.send_message(chat_id=user_id, text=a.__str__(), reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Elimina", callback_data=a.message_id)]]),parse_mode=ParseMode.MARKDOWN_V2)

    return SELECTING_ACTION


async def announce_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query.message.reply_markup.inline_keyboard[0][0].text == "Elimina":
        await query.answer()
        await query.edit_message_reply_markup(InlineKeyboardMarkup(
            [[InlineKeyboardButton("Confermi? ", callback_data=query.data)]]))

    else:

        with Database() as db:
            if not db.set_deleted(query.data):
                logger.error("Cannot set announce as deleted in Database")
                await query.answer(text=f"C'è stato un errore, l'annuncio non è stato rimosso")

            else:
                try:
                    await context.bot.delete_message(chat_id=channel_id, message_id=int(query.data))
                except BadRequest:
                    try:
                        await context.bot.edit_message_text("Annuncio non disponibile o scaduto 🧹", chat_id=channel_id, message_id=int(query.data))
                    except Exception:
                        pass

                await query.answer(text=f"L'annuncio è stato rimosso", show_alert=True)
                await query.delete_message()


