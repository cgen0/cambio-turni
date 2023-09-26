import json
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError
from telegram.ext import DictPersistence

from log.log import Log
from utils import utils

# callback data cache
CDCData = Tuple[List[Tuple[str, float, Dict[str, Any]]], Dict[str, str]]

# Enable logging


class DynamoDBHelper:
    def __init__(self, table_name: str) -> None:
        self.logger = Log()

        try:
            id, aws_key, region = utils.get_aws_credentials()
        except TypeError:
            self.logger.error("Error: Cannot read aws credentials from config.json")
            exit()

        """Initialize db class variables"""
        self.resource = boto3.resource('dynamodb', aws_access_key_id=id,
                                       aws_secret_access_key=aws_key,
                                       region_name=region)
        self.table = None
        self.exists(table_name)

    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.
        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self.resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                exists = False
            else:
                self.logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise
        else:
            self.table = table
        return exists

    def add_item(self, type: str, body: str):
        data = {
            "type": type,
            "data": body
        }
        self.table.put_item(Item=data)

    def get_item(self, key: str):
        response = self.table.get_item(Key={
            'type': key
        }
        )
        try:
            return response['Item']['data']
        except KeyError:
            return "{}"


class DynamoDBPersistence(DictPersistence):
    """Using DynamoDB to make user/chat/bot data persistent across reboots.

    Args:
        table_name (:obj:`str`, Optional) the dynamodb table name.
        session (:obj:`scoped_session`, Optional): sqlalchemy scoped session.
        on_flush (:obj:`bool`, optional): if set to :obj:`True` :class:`DynamoDBPersistence`
            will only update bot/chat/user data when :meth:flush is called.
        **kwargs (:obj:`dict`): Arbitrary keyword Arguments to be passed to
            the DictPersistence constructor.
    Attributes:
        store_data (:class:`PersistenceInput`): Specifies which kinds of data will be saved by this
            persistence instance.

    """

    def __init__(
            self,
            table_name: str,
            on_flush: bool = False,
            **kwargs: Any,
    ) -> None:
        self.logger = getLogger(__name__)
        self.on_flush = on_flush
        self.db_helper = DynamoDBHelper(table_name)

        self.logger.info("Loading persistence data from DynamoDB..")
        data = {}
        try:
            data = self.db_helper.get_item("persistence_data")
            data = json.loads(data)
            self.logger.info(f'data = {str(data)}')
        except ClientError as error:
            self.logger.error(
                f"error while get data from DynamoDB {error.response['Error']['Code'], error.response['Error']['Message']}")

        # data = data if data is not None else {}
        chat_data_json = data.get("chat_data", "")
        user_data_json = data.get("user_data", "")
        bot_data_json = data.get("bot_data", "")
        conversations_json = data.get("conversations", "{}")
        callback_data_json = data.get("callback_data_json", "")

        self.logger.info("Persistence data loaded successfully!")

        if not data:
            self.db_helper.add_item("persistence_data", json.dumps(data))

        super().__init__(
            **kwargs,
            chat_data_json=chat_data_json,
            user_data_json=user_data_json,
            bot_data_json=bot_data_json,
            callback_data_json=callback_data_json,
            conversations_json=conversations_json,
        )

    def _dump_into_json(self) -> Any:
        """Dumps data into json format for inserting in db."""
        self.logger.info("_dump_into_json")
        to_dump = {
            "chat_data": self.chat_data_json,
            "user_data": self.user_data_json,
            "bot_data": self.bot_data_json,
            "conversations": self.conversations_json,
            "callback_data": self.callback_data_json,
        }
        self.logger.info("Dumping %s", to_dump)
        return json.dumps(to_dump)

    def _update_database(self) -> None:
        self.logger.info("Updating persistence object...")
        try:
            self.db_helper.add_item("persistence_data", self._dump_into_json())
        except Exception as error:  # pylint: disable=W0703
            self.logger.error(
                "Failed to save persistence data in the database.\nLogging exception: ",
                exc_info=error,
            )

    async def update_conversation(
            self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Will update the conversations for the given handler.
        Args:
            name (:obj:`str`): The handler's name.
            key (:obj:`tuple`): The key the state is changed for.
            new_state (:obj:`tuple` | :obj:`any`): The new state for the given key.
        """
        self.logger.info("update_conversation")

        await super().update_conversation(name, key, new_state)
        if not self.on_flush:
            await self.flush()

    async def update_user_data(self, user_id: int, data: Dict) -> None:
        """Will update the user_data (if changed).
        Args:
            user_id (:obj:`int`): The user the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.user_data` ``[user_id]``.
        """
        self.logger.info("update_user_data")

        await super().update_user_data(user_id, data)
        if not self.on_flush:
            await self.flush()

    async def update_chat_data(self, chat_id: int, data: Dict) -> None:
        """Will update the chat_data (if changed).
        Args:
            chat_id (:obj:`int`): The chat the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.chat_data` ``[chat_id]``.
        """
        self.logger.info("update_chat_data")
        await super().update_chat_data(chat_id, data)
        if not self.on_flush:
            await self.flush()

    async def update_bot_data(self, data: Dict) -> None:
        """Will update the bot_data (if changed).
        Args:
            data (:obj:`dict`): The :attr:`telegram.ext.Dispatcher.bot_data`.
        """
        self.logger.info("update_bot_data")
        await super().update_bot_data(data)
        if not self.on_flush:
            await self.flush()

    async def update_callback_data(self, data: CDCData) -> None:
        """Will update the callback_data (if changed).
        Args:
            data (Tuple[List[Tuple[:obj:`str`, :obj:`float`, Dict[:obj:`str`, :class:`object`]]], \
                Dict[:obj:`str`, :obj:`str`]]): The relevant data to restore
                :class:`telegram.ext.CallbackDataCache`.
        """
        self.logger.info("update_callback_data")
        await super().update_callback_data(data)
        if not self.on_flush:
            await self.flush()

    async def flush(self) -> None:
        """Will be called by :class:`telegram.ext.Updater` upon receiving a stop signal. Gives the
        persistence a chance to finish up saving or close a database connection gracefully.
        """
        self._update_database()
        if not self.on_flush:
            self.logger.info("Closing database...")
