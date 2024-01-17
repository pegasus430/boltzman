import json
from flask import Flask
from flask import request
from api.aiapi import AIApi
from api.aiapi_external import AIApiExternal
from exceptions.exceptions import ServiceImageIsNotFound
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

api = AIApiExternal()

def auto_fail(value):
    print ("in decorator")
    def decorate(f):
        def f(*args, **kwargs):
            try:
                return f(*args,**kwargs)
            except Exception as ex:
                print (ex)
                return {
                    "error" : f"Internal Error for input: {ex}"
                }

        return f
    return decorate


@auto_fail
@app.route('/')
def index():
    return 'Capitalist Web server.'

@auto_fail
@app.route('/api/<endpoint>', endpoint='call_external_api',methods = ['POST'])
def call_external_api(endpoint):
    print (request.url_rule.rule)
    return api.runApi(request, endpoint)


app.run(host='0.0.0.0', port=8081)
