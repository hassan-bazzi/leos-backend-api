from flask import Flask
from flask_cors import CORS
import logging

from api.menu import menu_bp
from api.cart import cart_bp
from api.models.cart import Cart
from api.models.next_ids import NextIds

logging.basicConfig(filename='/log/backend.log',level=logging.DEBUG)

def create_app():
  app = Flask(__name__)

  stream_handler = logging.StreamHandler()
  stream_handler.setLevel(logging.INFO)
  app.logger.addHandler(stream_handler)

  CORS(app, supports_credentials=True)
  app.register_blueprint(menu_bp)
  app.register_blueprint(cart_bp)

  return app

def logger():
  return logging.getLogger('flask')

application = create_app()

# test
