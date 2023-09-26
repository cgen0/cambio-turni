import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from announce.announce import Announce
from log.log import Log
from utils.utils import get_aws_credentials

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = Log()


class Database:

    def __init__(self):
        try:
            id, aws_key, region = get_aws_credentials()
        except TypeError:
            print("Error: Cannot read aws credentials from config.json")
            exit()

        """Initialize db class variables"""
        self.resource = boto3.resource('dynamodb', aws_access_key_id=id,
                                       aws_secret_access_key=aws_key,
                                       region_name=region)
        self.table = None
        self.exists('announce')

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
                logger.error(
                    f"Couldn't check for existence of {table_name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
                raise
        else:
            self.table = table
        return exists

    def insert_announce(self, announce_instance):
        try:
            self.table.put_item(
                Item={
                    'message_id': announce_instance.message_id,
                    'user_id': announce_instance.user_id,
                    'user_name': announce_instance.user_name,
                    'type': announce_instance.type,
                    'category': announce_instance.category,
                    'date_start': announce_instance.date_start,
                    'date_end': announce_instance.date_end,
                    'info': announce_instance.info,
                    'deleted': 0,
                    'completed': 0
                })
            return True

        except ClientError as err:
            logger.error(f"Database ERROR {err}")
            return False

    def set_deleted(self, message_id):
        try:
            response = self.table.update_item(
                Key={'message_id': int(message_id)},
                UpdateExpression="set deleted=:r",
                ExpressionAttributeValues={
                    ':r': 1},
                ReturnValues="UPDATED_NEW")
            return True

        except ClientError as err:
            logger.error(f"Database ERROR {err}")
            return False

    def get_past_announces(self, timestamp):
        """
               Queries for announces which refers to a past date.

               :param timestamp: The limit date.
               :return: The list of expired announces.
               """
        try:
            response = self.table.scan(
                FilterExpression=Attr('date_end').between(1, int(timestamp) & Attr('deleted').eq(0)))
        except ClientError as err:
            logger.error(
                f"Couldn't query for announces expired in {timestamp}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
            return None
        else:
            ids = []
            for r in response['Items']:
                ids.append(int(r['message_id']))
            return ids

    def get_user_announces(self, user_id):
        try:
            response = self.table.scan(FilterExpression=Attr('user_id').eq(user_id) & Attr('deleted').eq(0))
        except ClientError as err:

            logger.error(
                f"Couldn't query for announces made by user {user_id}. Here's why:{err.response['Error']['Code']} : {err.response['Error']['Message']}")
            return None
        else:
            # cast Decimal to Integer
            formatted_item = [{k: (int(v) if isinstance(v, Decimal) else v) for k, v in d.items()} for d in
                              response['Items']]

            result = []
            for r in formatted_item:
                result.append(Announce(r))

            return result

    def __enter__(self):
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        pass
