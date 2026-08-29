from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.database import Database
# from schema import Paper
load_dotenv()
import os



uri = os.getenv("MONGODB_URI")

def connectdb(collection_name: str = "papers"):
    client: MongoClient = MongoClient(uri)
    database: Database[Paper] = client[collection_name]
    return database


if __name__ == "__main__":
    connectdb("papers")
