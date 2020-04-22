from flask import Flask
from api.menu import menu

app = Flask(__name__)
app.register_blueprint(menu)
