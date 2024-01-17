import jwt
from marshal import dumps
from sqlite3 import Timestamp
import string
from time import sleep
from utils.aiutils import validate
import json
from core.aibase import *
from exceptions.exceptions import *
from functools import wraps
import uuid
import datetime



class AIAccountSdk(object):
    def __init__(self, api) -> None:
        self.api = api
        self.sql_utils = api.sql_utils

    def generate_and_presist_user_token(self, account_id, user_json):
        user_json["timestamp"] = datetime.datetime.now().timestamp(),

        token = jwt.encode(user_json,
                           "password",
                           algorithm="HS256")
        self.sql_utils.insert("token", {
            "accountid": account_id,
            "token": token,
            "expiresat": datetime.datetime.now().timestamp() + 60 * 60 * 24 * 30 * 2  # months
        })

        return token

    def authorize_token(self, account_id, token):
        """ Checks the given token against database and returns true if token exists and not expired
            Throws either token expired or token doesnt exist exceptions

        Args:
            account_id: unique accound id
            token (string): jwt token
        """
        record = self.sql_utils.return_first_if_exists_with_where("token", {
            "accountid": account_id,
            "token": token}
        )

        if not record:
            raise AuthorizationTokenNotFound(
                f"account:{account_id} doesnt have token: {token}")

        token_expires_at = record[3]

        validate(token_expires_at > int(datetime.datetime.now().timestamp()),
                 "Expired Token.")

    def login(self, user, password):
        users = list(self.sql_utils.query_with_where("account", {
            "rootusername": user,
            "rootuserpassword": password
        }))

        if not len(users) == 1:
            raise AuthorizationError({
                "error": "Authorization Failed"
            })
        else:
            user = users[0]
            user_json = {
                "user_name": user[4],
                "account_id": user[1],
                "account_owner": user[2],
                "license_type": user[3]
            }
            token = self.generate_and_presist_user_token(user[1], user_json)
            return {
                "account_id": user[1],
                "user_name": user[4],
                "token": token
            }

    def logout(self, account_id, token):
        """ Expires the token for given account

        Args:
            account_id (string): account if
            token (string): token as string

        Returns:
            None
        """
        try:
            self.sql_utils.return_first_if_exists_with_where("token", {
                "accountid": account_id,
                "token": token}
            )
            self.sql_utils.update("token", {
                "expiresat" : -1
            },
                {
                "accountid": account_id,
                "token": token})

        except Exception as ex:
            print (ex)
            raise LogoutFailed("Log out failed.")


