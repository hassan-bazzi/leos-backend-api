from flask import Blueprint, jsonify
from flask_cors import CORS
from api.services.menu_service import get_menu_dict, get_item_dict

menu = Blueprint('menu', __name__)
CORS(menu, supports_credentials=True)


@menu.route('/menu')
def get_menu():
  return jsonify(get_menu_dict())


@menu.route('/menu/<int:item_id>')
def get_item(item_id):
  return jsonify(get_item_dict(item_id).get('data'))
