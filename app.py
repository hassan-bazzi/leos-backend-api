from flask import Flask
from flask_cors import CORS
from flywheel import Engine
import logging

from api.menu import menu
from api.cart import cart
from api.models.cart import Cart
from api.models.next_ids import NextIds

dynamo = Engine()
dynamo.register(Cart)
dynamo.register(NextIds)
dynamo.connect_to_region('us-east-1')
dynamo.create_schema()

def create_app():
  app = Flask(__name__)

  CORS(app, supports_credentials=True)
  app.register_blueprint(menu)
  app.register_blueprint(cart)

  return app

def logger():
  return logging.getLogger('flask')
