import bson
import pymongo


class MongoConnector:
    def __new__(cls, *args, **kwargs):
        if not getattr(MongoConnector, "__instance"):
            setattr(MongoConnector, "__instance", super(MongoConnector, cls).__new__(cls))
        return getattr(MongoConnector, "__instance")

    def __init__(self, dbname: str, username: str, password: str, auth_source: str, host: str = "localhost",
                 port: int = 8080):
        uri = f"mongodb://{username}:{password}@" \
              f"{host}:{port}/{dbname}?authSource={auth_source}"
        client = pymongo.MongoClient(uri)
        self.db = client.get_database()
        self.db.user.createIndex({"username": 1}, {"unique": True})
        self.db.token.createIndex({"token": 1}, {"unique": True})

    def add_user(self, username: str, password: str) -> str:
        users: pymongo.collection.Collection = self.db.user
        user_id = users.insert_one(
            {
                "username": username,
                "password": password,
            }
        ).inserted_id
        return str(user_id)

    def add_token(self, user_id: str, token: str) -> str:
        tokens: pymongo.collection.Collection = self.db.token
        token_id = tokens.insert_one(
            {
                "token": token,
                "user": bson.DBRef("user", bson.ObjectId(user_id)),
            }
        ).inserted_id
        return token_id

    def remove_token(self, token: str):
        tokens: pymongo.collection.Collection = self.db.token
        tokens.find_one_and_delete(
            {
                "token": token
            }
        )

    def get_tokens(self, user_id: str) -> list:
        tokens: pymongo.collection.Collection = self.db.token
        user_tokens = tokens.find(
            {
                "user.$id": bson.ObjectId(user_id),
            }
        )
        return [entry.token for entry in user_tokens]
