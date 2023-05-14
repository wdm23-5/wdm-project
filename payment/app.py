import atexit
import os
import time

import redis
from flask import Flask

from common.debug import wdm_assert_type, wdm_debug, wdm_debug_mask, wdm_print
from common.response import http_200_response, http_400_response, http_404_response, json_response
from common.scripts import lua_incrby_xx_ge_0

app = Flask("payment-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create_user')
def create_user():
    wdm_print(f'post payment/create_user at {time.time()}')
    # todo: validate user_id
    user_id = db.incr('user_id:counter')
    user_id = str(user_id)
    db.set(f'user_{user_id}:credit', 0)
    return json_response({'user_id': user_id})


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    wdm_print(f'get payment/find_user/{user_id} at {time.time()}')
    credit = db.get(f'user_{user_id}:credit')
    if credit is None:
        return http_404_response(wdm_debug_mask(f'user_{user_id}:credit nx'))
    wdm_assert_type(credit, bytes)
    credit = int(credit)
    return json_response({'user_id': user_id, 'credit': credit})


incrby_xx_ge_0 = db.register_script(lua_incrby_xx_ge_0)


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: str):
    wdm_print(f'post payment/add_funds/{user_id}/{amount} at {time.time()}')
    rst = incrby_xx_ge_0(keys=[f'user_{user_id}:credit'], args=[amount])
    done = rst is not None
    return json_response({'done': done})


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: str):
    wdm_print(f'post payment/pay/{user_id}/{order_id}/{amount} at {time.time()}')
    # todo: new whole transaction to validate user_id, order_id, amount
    rst = incrby_xx_ge_0(keys=[f'user_{user_id}:credit'], args=[f'-{amount}'])
    if rst is None:
        return http_400_response()
    db.set(f'user_{user_id}:order_{order_id}:amount', amount)  # todo: better data type
    return http_200_response()


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    wdm_print(f'post payment/cancel/{user_id}/{order_id} at {time.time()}')
    # todo: getdel is dumb. use custom transaction
    amount = db.getdel(f'user_{user_id}:order_{order_id}:amount')  # to be refactored in next iter
    if amount is None:
        return http_400_response()
    # amount == number OR amount == error
    return http_200_response()


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    wdm_print(f'post payment/status/{user_id}/{order_id} at {time.time()}')
    amount = db.get(f'user_{user_id}:order_{order_id}:amount')  # to be refactored in next iter
    paid = amount is not None
    return json_response({'paid': paid})


if wdm_debug():
    @app.post('/drop-database')
    def drop_database():
        db.flushdb()
        return http_200_response()
