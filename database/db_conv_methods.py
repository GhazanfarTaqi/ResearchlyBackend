from .connection import connectdb
from datetime import datetime, timezone

def get_conversation(conversation_id: str, user_id: str):
    connect = connectdb("conversations")
    conversation = connect.conversations.find_one({"conversation_id": conversation_id, "user_id": user_id})
    return conversation if conversation else None

def add_message_to_conversation(conversation_id: str, message: dict):
    connect = connectdb("conversations")
    result = connect.conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        }
    )
    return result.modified_count > 0

def add_conversation(conversation_id: str, user_id: str):
    connect = connectdb("conversations")
    conversation_data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "messages": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = connect.conversations.insert_one(conversation_data)
    return result.inserted_id is not None


def list_conversations(user_id: str):
    connect = connectdb("conversations")
    conversations = connect.conversations.find(
        {"user_id": user_id},
        {
            "_id": 0,
            "conversation_id": 1,
            "messages": 1,
            "created_at": 1,
            "updated_at": 1,
        },
    ).sort("updated_at", -1)

    return list(conversations)