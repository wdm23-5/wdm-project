import atexit
import json
import os
from http import HTTPStatus

import redis
from flask import Flask, Response

gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create/<user_id>')
def create_order(user_id):
    # todo: insert (order_id, user_id, timestamp)
    #  auto inc order_id
    order_id = 0
    response = Response(
        response=json.dumps({'order_id': order_id}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    # todo: delete (order_id, user_id, timestamp)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    return Response(status=HTTPStatus.OK)


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    # todo: select order_id from (order_id, user_id, timestamp) where order_id == order_id
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    # todo: select (order_id, item_id, amount) or else (order_id, item_id, 0)
    #  inc amount, cas
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    return Response(status=HTTPStatus.OK)


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    # todo: select order_id from (order_id, user_id, timestamp) where order_id == order_id
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    # todo: select amount from (order_id, item_id, amount)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    # todo: dec amount, mark but dont delete
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    return Response(status=HTTPStatus.OK)


@app.get('/find/<order_id>')
def find_order(order_id):
    # todo: select order_id from (order_id, user_id, timestamp) where order_id == order_id
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    user_id = 0

    # todo: call /payment/status/{user_id}/{order_id}
    #  next iter: async call
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    paid = False

    # todo: for each, select from (order_id, item_id, amount)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    item_ids = []
    amounts = []

    # todo: for each, select from (item_id, price)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    prices = []

    total_cost = sum(a * p for a, p in zip(amounts, prices))
    return Response(
        response=json.dumps({
            'order_id': order_id,
            'paid': paid,
            'items': item_ids,
            'user_id': user_id,
            'total_cost': total_cost
        }),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )


@app.post('/checkout/<order_id>')
def checkout(order_id):
    # todo: select from (order_id, user_id, timestamp) where order_id == order_id
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    # todo: for each, select from (order_id, item_id, amount)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    item_ids = []
    amounts = []

    # todo: for each, /payment/pay/{user_id}/{order_id}/{amount}
    #  next iter: reserve then sub, async call
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    # todo: for each, call /stock/subtract/{item_id}/{amount}
    #  next iter: reserve then sub, async call
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    # todo: update (order_id, paid)

    return Response(status=HTTPStatus.OK)
