import atexit
import os
import time

import redis
from flask import Flask

from common.debug import wdm_debug, wdm_debug_mask, wdm_print
from common.response import http_200_response, http_400_response, http_404_response, json_response
from common.scripts import lua_incrby_xx_ge_0
from common.type_check import int_else_none

app = Flask("stock-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/item/create/<price>')
def create_item(price: str):
    wdm_print(f'post stock/create/{price} at {time.time()}')

    if int_else_none(price) is None:
        return http_400_response()

    item_id = db.incr('item_id:counter')
    item_id = str(item_id)
    with db.pipeline() as pl:
        pl.set(f'item_{item_id}:price', price)
        pl.set(f'item_{item_id}:stock', 0)
        pl.execute()

    return json_response({'item_id': item_id})


@app.get('/find/<item_id>')
def find_item(item_id: str):
    wdm_print(f'get stock/find/{item_id} at {time.time()}')

    with db.pipeline() as pl:
        pl.get(f'item_{item_id}:price')
        pl.get(f'item_{item_id}:stock')
        rst = pl.execute()

    if len(rst) != 2:
        return http_404_response()
    price = int_else_none(rst[0])
    stock = int_else_none(rst[1])
    if price is None or stock is None:
        return http_404_response()

    return json_response({'stock': stock, 'price': price})


incrby_xx_ge_0 = db.register_script(lua_incrby_xx_ge_0)


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: str):
    wdm_print(f'post stock/add/{item_id}/{amount} at {time.time()}')

    if int_else_none(amount) is None:
        return http_400_response(wdm_debug_mask('amount is not int'))

    rst = incrby_xx_ge_0(keys=[f'item_{item_id}:stock'], args=[amount])
    if rst is None:
        return http_400_response(wdm_debug_mask('incrby_xx_ge_0 failed'))

    return http_200_response()


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: str):
    wdm_print(f'post stock/subtract/{item_id}/{amount} at {time.time()}')

    if int_else_none(amount) is None:
        return http_400_response(wdm_debug_mask('amount is not int'))

    rst = incrby_xx_ge_0(keys=[f'item_{item_id}:stock'], args=[f'-{amount}'])
    if rst is None:
        return http_400_response(wdm_debug_mask('incrby_xx_ge_0 failed'))

    return http_200_response()


if wdm_debug():
    @app.post('/drop-database')
    def drop_database():
        db.flushdb()
        return http_200_response()
