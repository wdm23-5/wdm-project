import atexit
import json
import os
from http import HTTPStatus

import redis
from flask import Flask, Response

app = Flask("stock-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/item/create/<price>')
def create_item(price: int):
    # todo: add or update (item_id, price)
    #  auto inc item_id
    item_id = 0
    response = Response(
        response=json.dumps({'item_id': item_id}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.get('/find/<item_id>')
def find_item(item_id: str):
    # todo: select (item_id, price)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    price = 0

    # todo: select (item_id, stock)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    stock = 0

    response = Response(
        response=json.dumps({
            'stock': stock,
            'price': price
        }),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    # todo: select (item_id, stock)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    return Response(status=HTTPStatus.OK)


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    # todo: call /add/<item_id>/-<amount>
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    return Response(status=HTTPStatus.OK)
