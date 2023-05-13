import atexit
import json
import os
import requests
from http import HTTPStatus

import redis
from flask import Flask, Response

gateway_url = os.environ['GATEWAY_URL']
STOCK_SERVICE_URL = f"{gateway_url}/stock"
ORDER_SERVICE_URL = f"{gateway_url}/orders"
# STOCK_SERVICE_URL = "http://stock-service:5000"
# PAYMENT_SERVICE_URL = "http://payment-service:5000"
# ORDER_SERVICE_URL = "http://order-service:5000"

app = Flask("payment-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()

atexit.register(close_db_connection)

# creates a user with 0 credit
# output: “user_id” - the user’s id
@app.post('/create_user')
def create_user():
    # todo: insert (user_id, credit)
    #  auto inc user_id
    user_id = db.incr('user_id')
    # user_data = {'user_id': user_id, 'credit': 0}
    db.hset('credit', f'user:{user_id}', 0)

    # order_calling = f"{ORDER_SERVICE_URL}/find/{order_id}"
    # response = requests.get(order_calling)
    # if response.status_code == 404:
    #     return Response(f"The order {order_id} does not exist", status=404)
    # order_user_id = response.json()['order_id']
    # db.hset('paid', f'order:{order_user_id}', False)

    response = Response(
        response=json.dumps({'user_id': user_id}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


# returns the user information
# output: “user_id” - the user’s id
#         “credit” - the user’s credit
@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    # todo: select (user_id, credit)
    credit = db.hget('credit', f'user:{user_id}')
    if credit is None: 
            raise NotImplementedError
    credit = int(credit)
    response = Response(
        response=json.dumps({
            'user_id': user_id,
            'credit': credit,
        }),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response

# adds funds (amount) to the user’s (user_id) account
# output: "done" (true/ false)
@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    # todo: select (user_id, credit)
    #  inc credit

    # check if the user exists
    user_exists = db.hexists('credit', f'user:{user_id}')
    if not user_exists:
        return Response(f"User {user_id} does not exist!", status= 404)
    db.hincrby('credit', f'user:{user_id}', amount)
    response = Response(
        response=json.dumps({'done': True}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response

# subtracts the amount of the order from the user’s credit
# (returns failure if credit is not enough)
@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    # # todo: call /find/<order_id>
    # success = True
    # if not success:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    # response = dict()
    #
    # if response['paid'] is True or response['user_id'] != user_id:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    #
    # # todo: select (user_id, credit)
    # success = True
    # if not success:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    # credit = 0
    #
    # # todo: atomic dec credit
    # #   cas credit
    # # return Response(status=HTTPStatus.BAD_REQUEST)
    #
    # return Response(status=HTTPStatus.OK)


    # check if the user exists
    user_exists = db.hexists('credit', f'user:{user_id}')
    if not user_exists:
        return Response(f"User {user_id} does not exist!", status=404)

    # check if the user has enough credit
    credit = db.hget('credit', f'user:{user_id}')
    if credit is None: 
            raise NotImplementedError
    credit = int(credit)

    # to do: check if the order exists
    order_calling = f"{ORDER_SERVICE_URL}/find/{order_id}"
    response = requests.get(order_calling)
   
    if response.status_code == 404:
        return Response(f"The order {order_id} does not exist", status=404)
    # order_user_id = response.json()['order_id']
#####################################################
    # todo :amount: call ['total_cost']
    total_cost = response.json()['total_cost']
    if credit < int(total_cost):
        return Response(f"User {user_id} does not have enough credit!", status= 403)

    # subtracts the amount of the order from the user’s credit
    db.hincrby('credit', f'user:{user_id}', -int(amount))

    # change the status of the payment (paid or not)
    db.hset('paid', f'order:{order_id}', True)

    response = Response(
        response=json.dumps({'done': True}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


# cancels payment made by a specific user for a specific order
@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    # # todo: call /find/<order_id>
    # success = True
    # if not success:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    # response = dict()
    #
    # if response['paid'] is False or response['user_id'] != user_id:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    #
    # # todo: select (user_id, credit)
    # success = True
    # if not success:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    # credit = 0
    #
    # # todo: atomic inc credit
    # #   cas credit
    # # return Response(status=HTTPStatus.BAD_REQUEST)
    #
    # # todo: for each, call /stock/add/{item_id}/{amount}
    #
    # # todo: update (order_id, paid)
    #
    # # bug
    #
    # return Response(status=HTTPStatus.OK)



    # check if the user exists
    user_exists = db.hexists('credit', f'user:{user_id}')
    if not user_exists:
        return Response(f"User {user_id} does not exist!", status=404)

    # check if the order exists
    order_calling = f"{ORDER_SERVICE_URL}/find/{order_id}"
    response = requests.get(order_calling)
    if response.status_code == 404:
        return Response(f"The order {order_id} does not exist", status=404)
    order_user_id = response.json()['order_id']
    total_cost = response.json()['total_cost']

    
    # check if response['paid'] is False
    paid_result = db.hget('paid', f'order:{order_id}')
    if paid_result == False:
        return Response(f"Order {order_id} payment status is False!", status=403)
    
    if user_id != order_user_id:
        return Response(f"The user {user_id} did not create order {order_id}!", status=403)

    # add the amount of the payment back to the user's credit
    credit = db.hget('credit', f'user:{user_id}')
    # credit = int(user_result[0])
    new_credit = credit + int(total_cost)
    db.hset(f'user:{user_id}', 'credit', new_credit)

    # delete the payment record from the DB
    db.delete(f'order:{order_id}')
    # change the payment status
    db.hset('paid', f'order:{order_id}', False)

    response = Response(
        response=json.dumps({'done': True}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


# returns the status of the payment (paid or not)
@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    # # todo: select (order_id, user_id)
    # success = True
    # if not success:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    # response_user_id = 0
    #
    # if response_user_id != user_id:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    #
    # # todo: select (order_id, paid)
    # success = True
    # if not success:
    #     return Response(status=HTTPStatus.BAD_REQUEST)
    # paid = False
    #
    # response = Response(
    #     response=json.dumps({'paid': paid}),
    #     status=HTTPStatus.OK,
    #     mimetype='application/json'
    # )
    # return response


    #check if the order exists
    order_result = db.hmget(f'user:{user_id}', 'user_id', 'amount')
    if not order_result:
        return Response(f"Order {order_id} does not exist!", status=404)

    # # check if the user has paid for the order
    # order_user_id, order_amount = order_result
    # if user_id != order_user_id:
    #     return Response(
    #     response=json.dumps({'done': False}),
    #     status=HTTPStatus.OK,
    #     mimetype='application/json'
    # )

    # order_calling = f"{ORDER_SERVICE_URL}/find/{order_id}"
    # response = requests.get(order_calling)
    # if response.status_code == 404:
    #     return Response(f"The order {order_id} does not exist", status=404)
    # order_user_id = response.json()['order_id']
    # db.hset('paid', f'order:{order_user_id}', False)

    paid = db.hget('paid', f'order:{order_id}')
    return Response(
        response=json.dumps({'paid': paid}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )

@app.get('/deletedb')
def delete_db():
    db.flushall()