from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.database import Database
# from schema import Paper
load_dotenv()
import os
from functools import lru_cache



uri = os.getenv("MONGODB_URI")

@lru_cache(maxsize=1)
def get_mongo_client():
    if not uri:
        raise RuntimeError("MONGODB_URI is not configured")

    return MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        maxPoolSize=50,
        retryWrites=True,
    )

def connectdb(collection_name: str = "papers"):
    client = get_mongo_client()
    database: Database[Paper] = client[collection_name]
    return database


if __name__ == "__main__":
    connectdb("papers")
