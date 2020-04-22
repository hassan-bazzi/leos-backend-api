
from flask import Blueprint, Response, request, jsonify

menu = Blueprint('menu', __name__)

@menu.route('/')
def get_menu():
 return jsonify({})
