import atexit
import os
import time
from http import HTTPStatus
from typing import Dict, List

import redis
import requests
from flask import Flask

from common.debug import wdm_assert, wdm_assert_type, wdm_debug, wdm_debug_mask, wdm_print
from common.response import http_200_response, http_400_response, http_404_response, jdumps, json_response, text_response
from common.scripts import lua_hdecr_ge_0

gateway_url = os.environ['GATEWAY_URL']

app = Flask('order-service')

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create/<user_id>')
def create_order(user_id: str):
    wdm_print(f'post orders/create/{user_id} at {time.time()}')
    # todo: validate user_id
    order_id = db.incr('order_id:counter')
    order_id = str(order_id)
    with db.pipeline() as pl:
        # todo: use script
        pl.hset('order_id:user_id', order_id, user_id)
        pl.set(f'order_{order_id}:paid', 0)
        pl.set(f'order_{order_id}:deleted', 0)
        pl.execute()
    # return http_500_response(wdm_debug_mask(jdumps({'user_id': user_id, 'order_id': order_id})))
    return json_response({'order_id': order_id})


@app.delete('/remove/<order_id>')
def remove_order(order_id: str):
    wdm_print(f'delete orders/remove/{order_id} at {time.time()}')
    # todo: validate order_id
    # op: BitFieldOperation = db.bitfield('order_id:status')
    # op.set('u2', f'#{order_id}', 0b11)
    # rst = op.execute()
    # prev_status: int = rst[0]
    prev_status = db.set(f'order_{order_id}:deleted', 1, get=True)
    if wdm_debug():
        if prev_status is None:
            # not exist
            return http_400_response(jdumps({'order_id': order_id, 'prev_status': -1}))
        else:
            wdm_assert_type(prev_status, bytes)
            prev_status = int(prev_status)
            if prev_status != 0:
                # already deleted
                return http_400_response(jdumps({'order_id': order_id, 'prev_status': prev_status}))
    return http_200_response()


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id: str, item_id: str):
    wdm_print(f'post orders/addItem/{order_id}/{item_id} at {time.time()}')
    # todo: validate order_id, item_id
    amount = db.hincrby(f'order_{order_id}:item_id:amount', item_id, 1)
    return http_200_response(wdm_debug_mask(jdumps({'order_id': order_id, 'item_id': item_id, 'amount': amount})))


hdecr_ge_0 = db.register_script(lua_hdecr_ge_0)


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id: str, item_id: str):
    wdm_print(f'delete orders/addItem/{order_id}/{item_id} at {time.time()}')
    # todo: validate order_id, item_id
    amount = hdecr_ge_0(keys=[f'order_{order_id}:item_id:amount'], args=[item_id])
    wdm_assert_type(amount, int)
    return http_200_response(wdm_debug_mask(jdumps({'order_id': order_id, 'item_id': item_id, 'amount': amount})))


# todo: multiple calls may return different number of items / cost.
#  require another api for consistent results for paid orders,
#  i.e. lazy evaluation & load from cache.
@app.get('/find/<order_id>')
def find_order(order_id: str):
    wdm_print(f'get orders/find/{order_id} at {time.time()}')
    # todo: validate order_id

    paid = db.get(f'order_{order_id}:paid')
    if paid is None:
        return http_404_response(wdm_debug_mask(f'order_{order_id}:paid nx'))
    wdm_assert_type(paid, bytes)
    paid = bool(int(paid))
    # todo: branch if already paid

    return _do_find_order(order_id, paid)


def _do_find_order(order_id: str, paid: bool):
    # todo: can be parallel

    user_id = db.hget('order_id:user_id', order_id)
    if user_id is None:
        return http_404_response(wdm_debug_mask(f'order_id:user_id {order_id} nx'))
    wdm_assert_type(user_id, bytes)
    user_id = user_id.decode('utf-8')

    item_amount = db.hgetall(f'order_{order_id}:item_id:amount')
    items: List[str] = []
    amounts: List[int] = []
    for k, v in item_amount.items():
        v = int(v)
        if v > 0:
            k = k.decode('utf-8')
            items.append(k)
            amounts.append(v)

    prices: List[int] = []
    stocks: List[int] = []
    for idx, item_id in enumerate(items):
        # todo: async / para
        resp = requests.get(f'{gateway_url}/stock/find/{item_id}')
        if resp.status_code != HTTPStatus.OK:
            return http_404_response(wdm_debug_mask(f'order_{order_id}:item_id:amount /stock/find/{item_id} nx'))
        jresp = resp.json()
        price = jresp['price']
        stock = jresp['stock']
        wdm_assert_type(price, int)
        wdm_assert_type(stock, int)
        prices.append(price)
        stocks.append(stock)

    # clamp amount
    # todo: no need to clamp. abort directly
    wdm_assert(len(amounts) == len(items) and len(prices) == len(items) and len(stocks) == len(items))
    item_ids: List[str] = []
    total_cost: int = 0
    for item_id, amount, price, stock in zip(items, amounts, prices, stocks):
        amount = min(stock, amount)
        item_ids.extend([item_id] * amount)
        total_cost += price * amount

    return json_response({
        'order_id': order_id,
        'paid': paid,
        'items': item_ids,
        'user_id': user_id,
        'total_cost': total_cost
    })


# todo: error if called concurrently
@app.post('/checkout/<order_id>')
def checkout(order_id: str):
    wdm_print(f'post orders/checkout/{order_id} at {time.time()}')
    # todo: validate order_id

    # todo: lock

    deleted = db.get(f'order_{order_id}:deleted')
    if deleted is None:
        return http_404_response(wdm_debug_mask(f'order_{order_id}:deleted nx'))
    wdm_assert_type(deleted, bytes)
    deleted = bool(int(deleted))
    if deleted:
        return http_400_response(wdm_debug_mask(f'order_{order_id}:deleted == 1'))

    paid = db.get(f'order_{order_id}:paid')
    if paid is None:
        return http_404_response(wdm_debug_mask(f'order_{order_id}:paid nx'))
    wdm_assert_type(paid, bytes)
    paid = bool(int(paid))
    if paid:
        return http_400_response(wdm_debug_mask(f'order_{order_id}:paid == 1'))

    resp = _do_find_order(order_id, paid)
    if resp.status_code != HTTPStatus.OK:
        return resp
    order_j = resp.json
    wdm_assert_type(order_j, dict)

    # todo: 2pc / occ

    resp = requests.post(f'{gateway_url}/payment/pay/{order_j["user_id"]}/{order_id}/{order_j["total_cost"]}')
    if resp.status_code != HTTPStatus.OK:
        # do not directly return the response from post
        return text_response(resp.text, resp.status_code)

    item_amount: Dict[str, int] = dict()
    for item_id in order_j['items']:
        item_amount[item_id] = item_amount.get(item_id, 0) + 1
    for item_id, amount in item_amount.items():
        resp = requests.post(f'{gateway_url}/stock/subtract/{item_id}/{amount}')
        if resp.status_code != HTTPStatus.OK:
            return text_response(resp.text, resp.status_code)

    db.set(f'order_{order_id}:paid', 1)

    return http_200_response()


if wdm_debug():
    @app.post('/drop-database')
    def drop_database():
        db.flushdb()
        return http_200_response()
