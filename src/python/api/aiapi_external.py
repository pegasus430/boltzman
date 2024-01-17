import json
import sys
import traceback
from api.aiapi import AIApi
from exceptions.exceptions import ExposedException
from utils.aiutils import make_sure
from utils.aiutils import validate

from api.account import AIAccountSdk


def get_parameters(func):
    keys = func.__code__.co_varnames[:func.__code__.co_argcount][::-1]
    sorter = {j: i for i, j in enumerate(keys[::-1])}
    if func.__defaults__:
        values = func.__defaults__[::-1]
    else:
        values = {}
    kwargs = {i: j for i, j in zip(keys, values)}
    sorted_args = tuple(
        sorted([i for i in keys if i not in kwargs], key=sorter.get)
    )

    sorted_kwargs = {
        i: kwargs[i] for i in sorted(kwargs.keys(), key=sorter.get)
    }
    return sorted_args, sorted_kwargs


api = AIApi()
account = AIAccountSdk(api)


def error(error_str):
    return {
        "status": "Error",
        "error_text": error_str
    }


def error_internal():
    return {
        "status": "Error",
        "error_text": "Internal Error."
    }


def error_parameter(payload):
    return {
        "status": "Error",
        "error_text": "Parameter Error.",
        "data": payload
    }


def response(payload):
    return {
        "status": "Success",
        "data": payload
    }


class AIApiExternal(object):
    def __init__(self):
        self.class_name = "AIApiExternal"

    def runApi(self, request, endpoint):
        #function_name = sys._getframe().f_code.co_name
        payload = {}
        try:
            payload = json.loads(request.data)
        except Exception:
            return error("POST data is not a valid JSON")

        #function_name = payload.get("end_point", None)
        function_name = endpoint
        params = payload.get("params", )
        if not "params" in payload:
            return error("Parameters are missing.")

        auth = payload.get("auth", )
        if not endpoint == "login" and not endpoint == "logout":
            if not "auth" in payload:
                return error("Auth is missing.")
            if not "account_id" in auth or not "token" in auth:
                return error("Malformed auth.")
            try:
                account.authorize_token(auth["account_id"], auth["token"])

            except ExposedException as ex:
                print(traceback.format_exc())
                return error(str(ex))

            except Exception as ex:
                print(traceback.format_exc())
                print(ex)
                return error_internal()

        api_func = None
        try:
            api_func = api.get_endpoint(function_name)
            if not callable(api_func):
                raise AttributeError()
        except AttributeError as ex:
            return error(f"{function_name} is not a valid API end point")

        m_params = get_parameters(api_func)

        if not function_name or (params is None and len(m_params[0]) > 1):
            return error_parameter(payload)

        missing_fields = [key for key in m_params[0]
                          if not key in params.keys() and not key == "self"]
        extra_fields = [key for key in params.keys(
        ) if not key in m_params[0] and not key in m_params[1].keys()]
        if len(missing_fields) > 0 or len(extra_fields) > 0:
            return error_parameter({
                "missing_fields": missing_fields,
                "extra_fields": extra_fields
            })
        try:
            return response(api_func(**params))

        except ExposedException as ex:
            print(traceback.format_exc())
            return error(str(ex))

        except Exception as ex:
            print(traceback.format_exc())
            print(ex)
            return error_internal()


if __name__ == "__main__":
    ex_api = AIApiExternal()

    payload = {'end_point': 'removeNetworks', 'params': {
        'source_service_id': "sdfsfdsfdf", 'network_ids': [1881]}}
    print(ex_api.runApi(payload))
