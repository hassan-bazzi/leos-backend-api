from flask import Blueprint, jsonify
from flask_cors import CORS
from api.services.menu import get_menu_dict, get_item_dict

menu_bp = Blueprint('menu', __name__)
CORS(menu_bp, supports_credentials=True)


@menu_bp.route('/menu')
def get_menu():
  return jsonify(get_menu_dict())


@menu_bp.route('/menu/<int:item_id>')
def get_item(item_id):
  return jsonify(get_item_dict(item_id).get('data'))
