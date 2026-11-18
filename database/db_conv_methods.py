from .connection import connectdb

def get_conversation(conversation_id: str, user_id: str):
    connect = connectdb("conversations")
    conversation = connect.conversations.find_one({"conversation_id": conversation_id, "user_id": user_id})
    return conversation if conversation else None

def add_message_to_conversation(conversation_id: str, message: dict):
    connect = connectdb("conversations")
    result = connect.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$push": {"messages": message}}
    )
    return result.modified_count > 0

def add_conversation(conversation_id: str, user_id: str):
    connect = connectdb("conversations")
    conversation_data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "messages": []
    }
    result = connect.conversations.insert_one(conversation_data)
    return result.inserted_id is not None