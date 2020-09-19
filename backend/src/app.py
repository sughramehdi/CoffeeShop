import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES
'''
GET /drinks
    it is a public endpoint
    it contains only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def get_drinks():
    try:
        selection = Drink.query.order_by(Drink.id).all()
        drinks = [drink.short() for drink in selection]
        return jsonify({
            'success': True,
            'drinks': drinks
        })
    except Exception:
        abort(404)


'''
GET /drinks-detail
    it requires the 'get:drinks-detail' permission
    it contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_details(payload):
    try:
        selection = Drink.query.order_by(Drink.id).all()
        drinks = [drink.long() for drink in selection]
        return jsonify({
            'success': True,
            'drinks': drinks
        })
    except Exception:
        abort(404)


'''
POST /drinks
    it creates a new row in the drinks table
    it requires the 'post:drinks' permission
    it contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
    where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    try:
        body = request.get_json()

        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        drink = Drink(title=new_title, recipe=json.dumps(new_recipe))
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception:
        abort(422)


'''
PATCH /drinks/<id>
    where <id> is the existing drink id
    it responds with a 404 error if <id> is not found
    it updates the corresponding row for <id>
    it requires the 'patch:drinks' permission
    it contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
    where drink is an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, drink_id):
    try:
        body = request.get_json()

        drink = Drink.query.filter(Drink.id == drink_id).first()
        if drink is None:
            abort(404)

        drink.title = body.get('title', drink.title)
        recipe = json.dumps(body.get('recipe'))
        drink.recipe = recipe if recipe != 'null' else drink.recipe

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception:
        abort(422)


'''
DELETE /drinks/<id>
    where <id> is the existing model id
    it responds with a 404 error if <id> is not found
    it deletes the corresponding row for <id>
    it requires the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id}
    where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).first()
        if drink is None:
            abort(404)
        drink.delete()
        return jsonify({
            'success': True,
            'delete': drink_id
        })
    except Exception:
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def badrequest(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(500)
def internalservererror(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal Server Error"
    }), 500
