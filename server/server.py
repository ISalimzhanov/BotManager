import datetime
import os

import pymongo.errors
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from bots.echoBot import EchoBot
from database_connectors.mongoConnector import MongoConnector
import binascii
import argparse

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = binascii.hexlify(os.urandom(30))
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=1)
jwt = JWTManager(app)
cache = {}  # temp


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    # toDo validate
    # toDo hashing
    try:
        mongo.add_user(data["username"], data["password"])
        return jsonify(
            {
                "ok": True,
                "message": "User registered successfully",
            }, 200
        )
    except pymongo.errors.PyMongoError as e:
        return jsonify(
            {
                "ok": False,
                "message": e,
            }, 400
        )


@app.route("/auth", methods=["POST"])
def auth_user():
    data = request.get_json()
    # toDo validate
    # toDo hashing
    user_id = mongo.get_user_id(data["username"], data["password"])
    try:
        if user_id:
            access_token = create_access_token(identity=user_id)
            refresh_token = create_refresh_token(identity=user_id)
            return jsonify(
                {
                    "ok": True,
                    "message": "Authorization passed successfully",
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }
                }
            ), 200
        else:
            return jsonify(
                {
                    "ok": False,
                    "message": "Authorization failed. Either password or login is incorrect",
                }
            ), 400
    except pymongo.errors.PyMongoError as e:
        return jsonify(
            {
                "ok": False,
                "message": e,
            }, 400
        )


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    data = {
        "access_token": create_access_token(identity=identity)
    }
    return jsonify({"ok": True, "data": data}), 200


@app.route("/bots", methods=["GET", "DELETE", "POST"])
@jwt_required
def bot():
    try:
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            msg = ""
            res = {}
            if request.method == "GET":
                res = mongo.get_tokens(user_id)
                msg = "List of user's bots' tokens is returned"
            elif request.method == "DELETE":
                mongo.remove_token(user_id, data["token"])
                msg = "Bot is stopped successfully"
                cache[data["token"]].join()
                del cache[data["token"]]
            else:
                mongo.add_token(user_id, data["token"])
                echo_bot = EchoBot(data["token"])
                cache[data["token"]] = echo_bot.run()
                msg = "Bot is launched successfully"
            return jsonify(
                {
                    "ok": True,
                    "message": msg,
                    "data": res,
                }, 200
            )
        except KeyError as e:
            return jsonify(
                {
                    "ok": False,
                    "message": "Bad request parameters",
                }, 400
            )
    except pymongo.errors.PyMongoError as e:
        return jsonify(
            {
                "ok": False,
                "message": e,
            }, 400
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-username", help="mongodb user's name", type=str)
    parser.add_argument("-password", help="mongodb user's password", type=str)
    parser.add_argument("-host", help="mongodb db's host", type=str)
    parser.add_argument("-port", help="mongodb db's port", type=int)
    parser.add_argument("-dbname", help="mongodb db's name", type=str)
    parser.add_argument("-auth_source", help="where credentials are stored", type=str)
    args = parser.parse_args()

    uri = f"mongodb://{args.username}:{args.password}@" \
          f"{args.host}:{args.port}/{args.dbname}?authSource={args.auth_source}"

    mongo = MongoConnector(uri)
    app.run()