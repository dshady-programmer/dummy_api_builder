"""
Define all user's authentication routes here
"""

from api.v1.views import app_views
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime, timedelta, timezone
from api.v1.auth.auth import login_required
from models import db, User
import jwt


@app_views.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()
    if not data:
        print("error")
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    if not all([email, password, confirm_password]):
        return (
            jsonify(
                {"error": "email, password, confirm_password fields are all required"}
            ),
            401,
        )
    if len(password) < 8 or password != confirm_password:
        return jsonify({"error": "Password validation failed"}), 401
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"message": "Account already exists, please login"}), 202
    hash_password = generate_password_hash(password)  # Hash password
    api_token = (
        f"{str(uuid.uuid4())}-{str(uuid.uuid4())}"  # api_token = api key for the user
    )
    user = User(email=email, password=hash_password, api_token=api_token)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Account registered successfully"}), 201


@app_views.route("/login", methods=["POST"])
def login():
    credentials = request.get_json()
    email = credentials.get("email")
    password = credentials.get("password")
    # print("email and password", email, password)

    if not all([email, password]):
        return jsonify({"error": "email and password fields are required"}), 401

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Incorrect email or password"}), 401
    new_public_id = None
    if check_password_hash(user.password, password):
        # Generates new public_id after every login
        if user.public_id:
            last_created = user.last_public_id_created
            # check if the last public key created is not more than 1 day
            if last_created and datetime.now() < (last_created + timedelta(days=1)):
                new_public_id = user.public_id
        if new_public_id is None:
            while True:
                # Ensuring public_id is unique before updating
                new_public_id = str(uuid.uuid4())
                check_associated_public_id = User.query.filter_by(
                    public_id=new_public_id
                ).first()
                if not check_associated_public_id:
                    break

            user.public_id = new_public_id
            user.last_public_id_created = datetime.now()
            db.session.commit()
        # Create jwt token
        from api.v1.app import app



        token = jwt.encode(
            {
                "public_id": new_public_id,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
                "jti": str(uuid.uuid4())
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return jsonify({"token": token}), 200
    return jsonify({"error": "Incorrect email or password"}), 401


@app_views.route("/me")
@login_required
def get_me(user):
    details = {"email": user.email, "api_token": user.api_token}
    return jsonify(details), 200


@app_views.route("/logout", methods=["POST"])
@login_required
def logout(user):
    user.public_id = None
    db.session.commit()
    return jsonify({"message": "Logged out"}), 200
