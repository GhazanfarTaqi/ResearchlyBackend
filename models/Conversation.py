import uuid
from database.db_conv_methods import *
class Conversation:
    def __init__(self, user_id: str, conversation_id: str = None):
        self.conversation_id = conversation_id if conversation_id is not None else  str(uuid.uuid4())
        self.user_id = user_id
        self.messages = []
        if conversation_id is None:
            add_conversation(self.conversation_id, self.user_id)
        else:
            conversation_data = get_conversation(conversation_id, self.user_id)
            if conversation_data:
                self.messages = conversation_data.get("messages", [])
            else:
                raise ValueError(f"Conversation with ID {conversation_id} not found.")

    def add_message(self, message: dict):
        self.messages.append(message)
        add_message_to_conversation(self.conversation_id, message)

    def get_messages(self):
        return self.messages

if __name__ == "__main__":
    # Example usage
    conversation = Conversation(user_id="user123")
    conversation.add_message("Hello, how are you?")
    conversation.add_message("I'm doing well, thank you!")
    
    print(f"Conversation ID: {conversation.conversation_id}")
    print(f"User ID: {conversation.user_id}")
    print("Messages:")
    for msg in conversation.get_messages():
        print(f"- {msg}")