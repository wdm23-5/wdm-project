import atexit
import json
import os
from http import HTTPStatus
from datetime import datetime
import redis
import requests
from flask import Flask, Response, request, jsonify
from typing import List


gateway_url = os.environ['GATEWAY_URL']
STOCK_SERVICE_URL = f"{gateway_url}/stock"
PAYMENT_SERVICE_URL = f"{gateway_url}/payment"
print(gateway_url,flush=True)

app = Flask("order-service")
print("--------- oreder start", flush=True)

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)

class Order:
    def __init__(self, order_id: int, user_id: int, items: List[int] = [], total_cost: int = 0, paid:bool = False):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total_cost = total_cost
        self.paid = paid

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": json.dumps(self.items),
            "paid": json.dumps(self.paid),
            "total_cost": self.total_cost
        }


@app.post('/create/<user_id>')
def create_order(user_id):
    # todo: check if the user exists
    # check if the user exists

    # Increment the order_id and save it to Redis.
    order_id = db.incr('order_id')
    new_order = {'order_id':order_id, 'user_id': user_id}
    # new_order = Order(order_id, user_id)
    # store to DB
    db.hset('user_id', f'order:{order_id}', user_id)

    # order_id = 0
    response = Response(
        response=json.dumps({'order_id': order_id}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    # todo: write the deleted status into paid
    success:bool = bool(db.delete(f'order:{order_id}'))
    if not success:
        return Response(status=HTTPStatus.NOT_FOUND)

    return Response(status=HTTPStatus.OK)

# async def get_payment_status(user_id,order_id):
#     # get the payment status by calling the payment service
#     payment_calling = f"{PAYMENT_SERVICE_URL}/status/{user_id}/{order_id}"
#     response = requests.post(payment_calling)
#     if response.status_code == 404:
#         return Response(f"Something went wrong with the order", status=404)
#     paid = response.json()['paid']
#     return paid

@app.get('/find/<order_id>')
def find_order(order_id):
    user_id_result = db.hget('user_id', f'order:{order_id}').decode('utf-8')
    if not user_id_result:
        return Response(f"The order {order_id} does not exist", status=404)

    # get the item ids and amounts from the order
    items = db.hgetall(f'order{order_id}')
    converted_items = {key.decode(): int(value) for key, value in items.items()}
    item_ids = list(converted_items.keys())
    item_ids = [int(id[5::]) for id in item_ids]
    amounts = list(converted_items.values())

    item_prices = []
    # get the price of the item by calling the stock service
    for item_id in item_ids:
        stock_calling = f"{STOCK_SERVICE_URL}/find/{str(item_id)}"
        response = requests.get(stock_calling)
        if response.status_code == 404:
            return Response(f"The item {item_id} does not exist", status=404)

        item_price = response.json()["price"]
        item_prices.append(int(item_price))

    total_cost = sum(a * p for a, p in zip(amounts, item_prices))

    # get the payment status by calling the payment service
    payment_calling = f"{PAYMENT_SERVICE_URL}/status/{user_id_result}/{order_id}"
    response = requests.post(payment_calling)
    print('response', response, flush =True  )
    if response.status_code != 200:
        return Response(f"Something went wrong with the order", status=404)
    paid = response.json()['paid']
    # if paid == None:
    #     paid = False

    # get the payment status asynchronously using a callback function
    # paid = False
    # async with aiohttp.ClientSession() as session:
    #     payment_status = await get_payment_status(user_id_result, order_id)
    #     if payment_status != False:
    #         paid = payment_status

    print('1111111',type(user_id_result),flush=True)
    print('2222222',type(order_id),flush=True)
    print('paid',paid,flush=True)


    order = {'order_id': str(order_id),
             'paid': paid,
             'items': converted_items,
             'user_id': str(user_id_result),
             'total_cost': total_cost}

    return order
    #
    # # convert order details from bytes to string
    # order_details_str = {k.decode('utf-8'): v.decode('utf-8') for k, v in order_result.items()}
    #
    # # create Order object from order details
    # order = Order(**order_details_str)
    #
    # # create response
    # response = Response(response=json.dumps({
    #     "order_id": order.order_id,
    #     "paid": order.paid,
    #     "items": order.items,
    #     "user_id": order.user_id,
    #     "total_cost": order.total_cost
    # }),
    # status=HTTPStatus.OK,
    # mimetype='application/json')
    # return response


# adds a given item in the order given
@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    # check if the order exists
    # if not db.hexists('user_id', f'order:{order_id}'):
    #     return Response(f"The order {order_id} does not exist", status=404)

    user_id_result = db.hget('user_id', f'order:{order_id}')
    if not user_id_result:
        return Response(f"The order {order_id} does not exist", status=404)
    # item = {'order_id':order_id, 'item_id': item_id}

    db.hincrby(f'order{order_id}', f'item:{item_id}', 1)
    return Response(f"The item {item_id} is added to order {order_id}", status=200)


# removes the given item from the given order
@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    user_id_result = db.hget('user_id', f'order:{order_id}')
    if not user_id_result:
        return Response(f"The order {order_id} does not exist", status=404)


    # check if the items you want to delete is actually in the order
    items_in_order = db.hkeys(f'order{order_id}')
    items_in_order = [item.decode() for item in items_in_order]
    print('items_in_order', items_in_order, flush=True)
    if f'item:{item_id}' not in items_in_order:
        return Response(f"The order {order_id} does not have item {item_id}!", status=404)

    db.hincrby(f'order{order_id}', f'item:{item_id}', -1)
    return Response(f"The item {item_id} is added to order {order_id}", status=200)




# make the payment (via calling the payment service),
# subtract the stock (via the stock service) and returns a status (success/failure).
@app.post('/checkout/<order_id>')
def checkout(order_id):
    # check if the order exists
    user_id_result = db.hget('user_id', f'order:{order_id}').decode('utf-8')
    if not user_id_result:
        return Response(f"The order {order_id} does not exist", status=404)

    # get the item ids and amounts from the order
    items = db.hgetall(f'order{order_id}')
    converted_items = {key.decode(): int(value) for key, value in items.items()}
    item_ids = list(converted_items.keys())
    item_ids = [int(id[5::]) for id in item_ids]
    amounts = list(converted_items.values())

    # check if the order has more than 1 item
    if sum(amounts) == 0:
        return Response(f"The order {order_id} is empty!", status=400)

    # check if the order has already been paid (call payment status)
    payment_calling = f"{PAYMENT_SERVICE_URL}/status/{user_id_result}/{order_id}"
    response = requests.post(payment_calling)
    if response.status_code == 404:
        return Response(f"Something went wrong with the order", status=404)
    paid = response.json()['paid']
    if paid == 'True':
        return Response(f"The order {order_id} is already paid!", status=400)

    # total_cost = find_order(order_id)

    item_prices = []
    # get the price of the item by calling the stock service
    for item_id in item_ids:
        stock_calling = f"{STOCK_SERVICE_URL}/find/{str(item_id)}"
        response = requests.get(stock_calling)
        if response.status_code == 404:
            return Response(f"The item {item_id} does not exist", status=404)

        item_price = response.json()["price"]
        item_prices.append(int(item_price))

    total_cost = sum(a * p for a, p in zip(amounts, item_prices))

    # make the payment (call remove_credit)
    remove_credit_calling = f"{PAYMENT_SERVICE_URL}/pay/{user_id_result}/{str(order_id)}/{total_cost}"
    response = requests.post(remove_credit_calling)
    if response.status_code != 200:
        return Response(f"Something went wrong with the payment...", status=response.status_code)

    # subtract the stock(call remove_stock)
    for i in range(len(item_ids)):
        stock_calling = f"{STOCK_SERVICE_URL}/subtract/{str(item_ids[i])}/{amounts[i]}"
        response = requests.post(stock_calling)
        if response.status_code != 200:
            return Response(f"Something went wrong with the stock...", status=response.status_code)

    return Response(f"Order {order_id} is paid successfully", status=200)
    # # update the payment status
    # db.hset(f'order:{order_id}', 'paid', True)



    # order_result = db.hgetall(f'order:{order_id}')
    # # convert order details from bytes to string
    # order_details_str = {k.decode('utf-8'): v.decode('utf-8') for k, v in order_result.items()}
    # # create Order object from order details
    # order = Order(**order_details_str)
    # order.order_id = int(order.order_id)
    # order.user_id = int(order.user_id)
    # order.total_cost = int(order.total_cost)
    # order.paid = bool(order.paid)
    # # order.items = json.loads(order.items)
    #
    # # check if the order has more than 1 item
    # if not order.items:
    #     return Response(f"The order {order_id} is empty!", status=400)
    #
    # # check if the order is paid
    # if order.paid == True:
    #     return Response(f"The order {order_id} is already paid!", status=400)
    #
    # # make the payment (via calling the payment service)
    # payment_calling = f"{PAYMENT_SERVICE_URL}/pay/{order.user_id}/{order_id}/{order.total_cost}"
    # response = requests.post(payment_calling)
    # if response.status_code != 200:
    #     return Response(f"Something went wrong with the payment...", status=response.status_code)
    #
    # # subtract the stock (via the stock service)
    # for item_id in order.items:
    #     stock_calling = f"{STOCK_SERVICE_URL}/subtract/{item_id}/1"
    #     response = requests.post(stock_calling)
    #     if response.status_code != 200:
    #         return Response(f"Something went wrong with the stock...", status=response.status_code)
    #
    
    # # update the payment status
    # db.hset(f'order:{order_id}', 'paid', True)

@app.get('/deletedb')
def delete_db():
    db.flushall()