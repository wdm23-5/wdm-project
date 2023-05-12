import atexit
import json
import os
from http import HTTPStatus

import redis
from flask import Flask, Response

app = Flask("stock-service")
app = Flask("stock-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)

def _____():
    dataset = dict()
    
    item_id = 1
    dataset[item_id] = {'stock': 10, 'price':20}


@app.post('/item/create/<price>')
def create_item(price: int):
    # todo: add or update (item_id, price)
    #  auto incr item_id by 1 
    item_id = db.incr('item_id')
    # item = {'item_id': item_id, 'stock': 0, 'price': price}
    # db.hset(f'item:{item_id}', mapping=item)  
    
    # price_map = dict()
    # price_map[item_id] = price
    
    db.hset('price', f'item{item_id}', price)
    db.hset('stock', f'item{item_id}', 0)
      
    response = Response(
        response=json.dumps({'item_id': item_id}),
        status=HTTPStatus.OK,
        mimetype='application/json'
    )
    return response


@app.get('/find/<item_id>')
def find_item(item_id: str):
    # todo: select (item_id, price)
    # value = db.exists(f'item:{item_id}')
    # print('value', value, flush=True)
    
    print('hget', db.hget('stock', f'item{item_id}'), flush=True)
    stock = db.hget('stock', f'item{item_id}')
    if stock is None: 
            raise NotImplementedError
    stock = int(stock)

    price = db.hget('price', f'item{item_id}')
    if price is None: 
            raise NotImplementedError
    price = int(price)
    print('stock, price', stock, price, flush=True)
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
    db.hincrby('stock', f'item{item_id}', amount)
    # success = True
    # if not success:
    #     return Response(status=HTTPStatus.NOT_FOUND)

    return Response(status=HTTPStatus.OK)


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    # todo: call /add/<item_id>/-<amount>
    stock = int(db.hget('stock', f'item{item_id}'))
    # print('stock', stock,  flush=True)
    if stock < int(amount):
        return Response(status=HTTPStatus.NOT_FOUND) 
    else:
         db.hincrby('stock', f'item{item_id}', -int(amount))
        #  stock = int(db.hget(f'item:{item_id}', 'stock'))
        #  print('stock1', stock,  flush=True)
         return Response(status=HTTPStatus.OK)
 
    
# delete 
@app.get('/deletedb')
def delete_db(item_id: str):
    db.flushall()


