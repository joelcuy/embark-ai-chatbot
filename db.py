import firebase_admin
from firebase_admin import credentials, firestore

from constants import *

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


def create_user(user_id, data):
    db.collection(TABLE_USERS).document(str(user_id)).set(data)


def read_user(user_id):
    result = db.collection(TABLE_USERS).document(str(user_id)).get()
    if result.exists:
        return result.to_dict()
    return None


def update_user(user_id, newData):
    db.collection(TABLE_USERS).document(str(user_id)).update(newData)
