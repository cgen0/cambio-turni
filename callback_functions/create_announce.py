from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (ContextTypes, )

from announce.announce import Announce
from data.keyboards import announce_type_keyboard, announce_category_keyboard, announce_confirm_keyboard, \
    starting_keyboard
from data.states import SELECTING_ACTION, NEW_ANNOUNCE_TEXT, NEW_ANNOUNCE_TYPE, NEW_ANNOUNCE_START_DATE_WANTS, \
    NEW_ANNOUNCE_START_DATE_GIVE, NEW_ANNOUNCE_START_TIME, NEW_ANNOUNCE_GROUP_DATE, NEW_ANNOUNCE_DONE, \
    NEW_ANNOUNCE_CONFIRM
from database.database import Database
from log.log import Log
from utils.utils import is_time_valid, validate_date_and_guess_year, get_channel

channel_id = get_channel()
# Enable logging
logger = Log()


async def start_new_announce(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Chiede all'utente se cerca o cede un turno."""

    if 'name' not in context.user_data.keys():
        reply_text = (
            'Prima di incominciare, ho bisogno del tuo nominativo. Per inserirlo premi sul tasto "Profilo"'
        )
        markup = ReplyKeyboardMarkup([["Profilo"]], one_time_keyboard=False)
        await update.message.reply_text(reply_text, reply_markup=markup)
        return SELECTING_ACTION

    reply_text = f"Cedi o cerchi un turno?"
    markup = ReplyKeyboardMarkup(announce_type_keyboard, one_time_keyboard=False)
    await update.message.reply_text(reply_text, reply_markup=markup)
    return NEW_ANNOUNCE_TYPE


async def announce_type_wants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva il tipo di turno e chiede all'utente la categoria del turno."""
    user = update.message.from_user.id
    text = update.message.text
    context.user_data["new_announce"] = {}
    context.user_data["new_announce"]["user_id"] = user
    context.user_data["new_announce"]["user_name"] = context.user_data['name']
    context.user_data["new_announce"]["type"] = "Cerco"
    reply_text = f"Qual è la categoria del turno?"
    markup = ReplyKeyboardMarkup([["Riposo", "RFD"]], one_time_keyboard=False)

    await update.message.reply_text(reply_text, reply_markup=markup)
    return NEW_ANNOUNCE_START_DATE_WANTS


async def announce_type_give(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva il tipo di turno e chiede all'utente la categoria del turno."""
    user = update.message.from_user.id
    text = update.message.text
    context.user_data["new_announce"] = {}
    context.user_data["new_announce"]["user_id"] = user
    context.user_data["new_announce"]["user_name"] = context.user_data['name']
    context.user_data["new_announce"]["type"] = "Cedo"
    reply_text = f"Qual è la categoria del turno?"
    markup = ReplyKeyboardMarkup(announce_category_keyboard, one_time_keyboard=False)

    await update.message.reply_text(reply_text, reply_markup=markup)
    return NEW_ANNOUNCE_START_DATE_GIVE


async def announce_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva la categoria del turno e chiede all'utente data e ora di inizio turno."""
    """***Per non mettere anche l'anno assumo che se giorno e mese sono antecedenti ad oggi allora l'anno è il prossimo***"""

    text = update.message.text
    context.user_data["new_announce"]["category"] = text
    if text == "Ferie":
        context.user_data["new_announce"]["time_start"] = "00:00"
        context.user_data["new_announce"]["time_end"] = "00:00"
        reply_text = f"""Qual è la data di inizio turno?\n\nFormato: "gg/mm" """
        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return NEW_ANNOUNCE_START_TIME
    if text == "Riposo":
        reply_text = f"""Qual è la data?\n\nFormato: "gg/mm" """
    else:
        reply_text = f"""Qual è la data di inizio turno?\n\nFormato: "gg/mm" """

    await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    return NEW_ANNOUNCE_START_TIME


async def announce_vacation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva la categoria dell'annuncio e chiede all'utente di indicare i periodi di ferie da scambiare."""

    text = update.message.text
    context.user_data["new_announce"]["category"] = text
    context.user_data["new_announce"]["time_start"] = "00:00"
    context.user_data["new_announce"]["time_end"] = "00:00"
    context.user_data["new_announce"]["date_start"] = "01-01-1970"
    if text == "Ferie":
        reply_text = f"""Indica il periodo di ferie che vorresti cedere e quello che cerchi."""

    await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    return NEW_ANNOUNCE_TEXT


async def announce_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva la categoria dell'annuncio e chiede all'utente di indicare i periodi di ferie da scambiare."""

    text = update.message.text
    context.user_data["new_announce"]["category"] = text
    context.user_data["new_announce"]["time_start"] = "00:00"
    context.user_data["new_announce"]["time_end"] = "23:59"

    reply_text = f"""Indica data di inizio e data di fine stecca.\n\nFormato: "gg/mm - gg/mm" """
    await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    return NEW_ANNOUNCE_GROUP_DATE


async def announce_group_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva la data di inzio e fine della stecca e chiede all'utente i dettagli sui turni."""

    try:
        s, e = update.message.text.replace(" ", "").split("-")
        sd = validate_date_and_guess_year(s)
        ed = validate_date_and_guess_year(e)

        if not sd or not ed:
            reply_text = f"Le date inserita non sono corrette, riprova"
            await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
            return NEW_ANNOUNCE_GROUP_DATE
        else:
            context.user_data["new_announce"]["date_start"] = int(datetime.strptime(sd, "%d-%m-%Y").timestamp())
            context.user_data["new_announce"]["date_end"] = int(datetime.strptime(ed, "%d-%m-%Y").timestamp())
            reply_text = f"""Indica ora in dettaglio i turni che si cedono e ciò che cerchi con eventuali vincoli orari."""

            await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
            return NEW_ANNOUNCE_TEXT

    except ValueError:
        reply_text = f"Le date inserita non sono corrette, riprova"
        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return NEW_ANNOUNCE_GROUP_DATE


async def announce_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva la data di inzio del turno e chiede all'utente ora di inizio e fine turno."""
    text = update.message.text
    v = validate_date_and_guess_year(text)
    if not v:
        reply_text = f"La data inserita non è corretta, riprova"
        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return NEW_ANNOUNCE_START_TIME

    else:
        context.user_data["new_announce"]["date_start"] = v

        if context.user_data["new_announce"]["category"] == "Riposo":
            context.user_data["new_announce"]["time_start"] = "00:00"
            context.user_data["new_announce"]["time_end"] = "23:59"
            if context.user_data["new_announce"]["type"] == "Cerco":
                reply_text = f"""Indica ora info sul turno che cedi ed eventuali date per il recupero del riposo"""
            else:
                reply_text = f"""Scrivi cosa cerchi in cambio ed eventuali informazioni aggiuntive"""

            await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
            return NEW_ANNOUNCE_TEXT

        if context.user_data["new_announce"]["category"] == "RFD":

            if context.user_data["new_announce"]["type"] == "Cedo":
                reply_text = (f"""Quali sono gli orari di inizio e fine turno (del giorno successivo)?\n"""
                              """\nFormato: "hh:mm - hh:mm" """)

            elif context.user_data["new_announce"]["type"] == "Cerco":
                context.user_data["new_announce"]["time_start"] = "00:00"
                context.user_data["new_announce"]["time_end"] = "23:59"
                reply_text = (f"""Indica ora in dettaglio i turni che cedi ed eventuali info aggiuntive sull'RFD che cerchi""")
                await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
                return NEW_ANNOUNCE_TEXT

        else:
            reply_text = f"""Quali sono gli orari di inizio e fine turno?\n\nFormato: "hh:mm - hh:mm" """

        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return NEW_ANNOUNCE_DONE


async def announce_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva l'orario del turno e chiede all'utente il testo facoltativo."""
    text = update.message.text

    if not is_time_valid(text):
        reply_text = f"Gli orari inseriti non sono corretti, riprova"
        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return NEW_ANNOUNCE_DONE

    else:
        s, e = text.replace(" ", "").split("-")
        context.user_data["new_announce"]["time_start"] = s
        context.user_data["new_announce"]["time_end"] = e
        if context.user_data["new_announce"]["type"] == "Cerco":
            if context.user_data["new_announce"]["category"] == "RFD":
                reply_text = f"""Indica ora in dettaglio i turni che cedi ed eventuali info aggiuntive sull'RFD che cerchi"""
            if context.user_data["new_announce"]["category"] == "Riposo":
                reply_text=f"""Indica ora info sul turno che cedi ed eventuali date per il recupero del riposo"""

            else:
                reply_text = f"""Indica ora cosa cedi in cambio ed eventuali informazioni aggiuntive"""
        else:
            if context.user_data["new_announce"]["category"] == "Turno":
                reply_text = f"""Indica ora le info aggiuntive sul turno che cedi e su quello che cerchi con eventuali vincoli orari"""

            elif context.user_data["new_announce"]["category"] == "Riserva":
                reply_text = f"""Indica ora eventuali info aggiuntive sulla riserva che cedi e su quello che cerchi con eventuali vincoli orari. Se per RFD specificarlo indicando anche il turno del giorno successivo"""
            elif context.user_data["new_announce"]["category"] == "RFD":
                reply_text = f"""Indica ora info aggiuntive sull'RFD che cedi e su ciò che cerchi con eventuali vincoli orari"""
            else: reply_text = f"""Indica ora cosa cerchi in cambio ed eventuali informazioni aggiuntive"""

        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return NEW_ANNOUNCE_TEXT


async def announce_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva le informazioni se sono state inserite, mostra all'utente il riepilogo e chiede conferma."""
    text = update.message.text
    if text == "":
        reply_text = f"""Questo campo è obbligatorio."""
        await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
        return NEW_ANNOUNCE_TEXT

    context.user_data["new_announce"]["info"] = text
    context.user_data['new_announce']['message_id'] = None

    reply_text = f"Questo è il riepilogo dell'annuncio: \n{Announce(context.user_data['new_announce']).to_message(update.message.from_user.username)}"
    markup = ReplyKeyboardMarkup(announce_confirm_keyboard, one_time_keyboard=False)

    await update.message.reply_text(reply_text, reply_markup=markup,
                                    parse_mode=ParseMode.MARKDOWN_V2)
    return NEW_ANNOUNCE_CONFIRM


async def announce_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Chiede conferma, salva l'annuncio e lo invia sul canale
    altrimenti annulla l'operazione e rimanda al menu iniziale"""

    text = update.message.text
    if text == "✅ Conferma":
        """Saving announce on db"""
        a = Announce(context.user_data['new_announce'])
        sent = await context.bot.send_message(chat_id=channel_id,
                                              text=a.to_message(update.message.from_user.username), parse_mode=ParseMode.MARKDOWN_V2)
        a.message_id = sent.id

        with Database() as db:
            if not db.insert_announce(a):
                await context.bot.delete_message(chat_id=channel_id, message_id=sent.id)
                logger.error("Cannot save announce in Database")
                reply_text = f"C'è stato un errore, l'annuncio non è stato pubblicato"

            else:
                reply_text = f"Annuncio pubblicato con successo"

    else:
        context.user_data.pop("new_announce", None)
        reply_text = f"Annuncio eliminato"

    markup = ReplyKeyboardMarkup(starting_keyboard, one_time_keyboard=False)
    await update.message.reply_text(reply_text, reply_markup=markup)
    context.user_data.pop("new_announce", None)
    return SELECTING_ACTION
