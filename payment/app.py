import atexit
import json
import os
from http import HTTPStatus

import redis
from flask import Flask, Response

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
    # todo: insert (user_id, credit)
    #  auto inc user_id
    user_id = 0
    response = Response(
        response=json.dumps({'user_id': user_id}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    # todo: select (user_id, credit)
    success = True
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)
    credit = 0

    response = Response(
        response=json.dumps({
            'user_id': user_id,
            'credit': credit,
        }),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    # todo: select (user_id, credit)
    #  inc credit
    success = True

    response = Response(
        response=json.dumps({'done': success}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    # todo: call /find/<order_id>
    success = True
    if not success:
        return Response(status=HTTPStatus.BAD_REQUEST)
    response = dict()

    if response['paid'] is True or response['user_id'] != user_id:
        return Response(status=HTTPStatus.BAD_REQUEST)

    # todo: select (user_id, credit)
    success = True
    if not success:
        return Response(status=HTTPStatus.BAD_REQUEST)
    credit = 0

    # todo: atomic dec credit
    #   cas credit
    # return Response(status=HTTPStatus.BAD_REQUEST)

    return Response(status=HTTPStatus.OK)


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    # todo: call /find/<order_id>
    success = True
    if not success:
        return Response(status=HTTPStatus.BAD_REQUEST)
    response = dict()

    if response['paid'] is False or response['user_id'] != user_id:
        return Response(status=HTTPStatus.BAD_REQUEST)

    # todo: select (user_id, credit)
    success = True
    if not success:
        return Response(status=HTTPStatus.BAD_REQUEST)
    credit = 0

    # todo: atomic inc credit
    #   cas credit
    # return Response(status=HTTPStatus.BAD_REQUEST)

    # todo: for each, call /stock/add/{item_id}/{amount}

    # todo: update (order_id, paid)

    # bug

    return Response(status=HTTPStatus.OK)


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    # todo: select (order_id, user_id)
    success = True
    if not success:
        return Response(status=HTTPStatus.BAD_REQUEST)
    response_user_id = 0

    if response_user_id != user_id:
        return Response(status=HTTPStatus.BAD_REQUEST)

    # todo: select (order_id, paid)
    success = True
    if not success:
        return Response(status=HTTPStatus.BAD_REQUEST)
    paid = False

    response = Response(
        response=json.dumps({'paid': paid}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response
