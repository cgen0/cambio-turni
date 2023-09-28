import asyncio
import json
import locale
from warnings import filterwarnings

from telegram.ext import (Application, CommandHandler, ConversationHandler, MessageHandler,
                          CallbackQueryHandler,
                          filters, )
from telegram.warnings import PTBUserWarning

from callback_functions.base import *
from callback_functions.create_announce import *
from callback_functions.manage_announces import *
from callback_functions.profile import *
from data.states import *
from persistance.dynamopersistance import DynamoDBPersistence
from utils.utils import get_token

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

channel_id = get_channel()
locale.setlocale(locale.LC_ALL, 'it_IT.utf8')

# Enable logging
logger = Log()



async def main(event, context):
    """Run the bot."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                MessageHandler(filters.TEXT & filters.Regex("^➕ Nuovo annuncio$"), start_new_announce),
                MessageHandler(filters.TEXT & filters.Regex("^🗑️ Elimina annuncio$"), get_announces),
                MessageHandler(filters.TEXT & filters.Regex("^👥 Profilo$"), edit_profile),
                CallbackQueryHandler(announce_delete)],

            FORCE_PROFILE: [MessageHandler(filters.TEXT & filters.Regex("^👥 Profilo$"), edit_profile),
                            MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^👥 Profilo$"),
                                           force_profile)],

            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_profile)],

            NEW_ANNOUNCE_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^➡️ Cerco$"), announce_type_wants),
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^Cedo ➡️$"), announce_type_give)],

            NEW_ANNOUNCE_START_DATE_GIVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^(Turno|Riserva|RFD)$"),
                               announce_start_date),
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^Ferie$"), announce_vacation),
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^Stecca$"),
                               announce_group)],
            NEW_ANNOUNCE_GROUP_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               announce_group_date)],
            NEW_ANNOUNCE_START_DATE_WANTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^(Riposo|RFD)$"), announce_start_date)],

            NEW_ANNOUNCE_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, announce_time)],

            NEW_ANNOUNCE_DONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, announce_done)],

            NEW_ANNOUNCE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, announce_text)],

            NEW_ANNOUNCE_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^(✅ Conferma|❌ Cancella)$"),
                               announce_confirm)]
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        name="conversations",
        persistent=True,
    )
    persistence = DynamoDBPersistence(table_name="persistence",on_flush=False)

    token = get_token()
    if not token:
        logger.error("Impossibile caricare il TOKEN, verificare che sia presente in config.json")
        exit()
    application = Application.builder().token(token).persistence(persistence).build()
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    try:
        await application.initialize()
        await application.process_update(
            Update.de_json(json.loads(event["body"]), application.bot)
        )
        await application.update_persistence()

        return {
            'statusCode': 200,
            'body': 'Success'
        }

    except Exception as exc:
        return {
            'statusCode': 500,
            'body': 'Failure'
        }
async def clean_old_announces(event, context):
    token = get_token()
    channel_id = get_channel()

    if not token:
        return {
            'statusCode': 500,
            'body': 'Failure'
        }

    application = Application.builder().token(token).build()
    with Database() as db:
        now = datetime.now().timestamp()
        ids = db.get_past_announces(now)

        if ids:
            for i in ids:
                try:
                    await application.bot.delete_message(chat_id=channel_id, message_id=int(i))
                    db.set_deleted(int(i))

                except BadRequest:
                    try:
                        await application.bot.edit_message_text("Annuncio non disponibile o scaduto 🧹",
                                                                chat_id=channel_id, message_id=int(i))
                        db.set_deleted(int(i))

                    except Exception as e:
                        print(e)
    return {
        'statusCode': 200,
        'body': 'Success'
    }


def lambda_handler(event, context):
    if 'source' in event and event['source'] == 'aws.events':
        logger.info(f"arrivato messaggio {event['source']} {context}")

        return asyncio.get_event_loop().run_until_complete(clean_old_announces(event,context))
    else:
        return asyncio.get_event_loop().run_until_complete(main(event, context))
