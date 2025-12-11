from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()
from api.v1.views import app_views
from flask_migrate import Migrate
from . import create_app

app = create_app()
app.register_blueprint(app_views)
CORS(app,resources={r"/*": {"origins": r"*"}})
migrate = Migrate()


@app.route("/")
def index():
    return jsonify({"message": "Welcome to dummy api"})
