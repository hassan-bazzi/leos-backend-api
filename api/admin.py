import logging
import os
from flask import Blueprint, request, jsonify, make_response
from flask_cors import CORS

from ..api.models.cart import Cart

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)
CORS(admin_bp, supports_credentials=True)


@admin_bp.route('/admin/cart', methods=['GET'])
def cart_controller():

    return jsonify(cart.as_json())
