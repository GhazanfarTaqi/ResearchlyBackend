import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from models.Conversation import Conversation
from agents.main_agent import run_agent


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://researchlyfrontend.vercel.app"
        # Add Vercel URL after deploying frontend
        # "https://researchly.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    conversation_id: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str 
    user_id: str 
    conversation_id: str

class CreateConversationRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/conversation",response_model=CreateConversationRequest)
def conversation(request:CreateConversationRequest):
    conversation = Conversation(request.user_id)
    return ChatResponse(reply="Conversation started", user_id=request.user_id, conversation_id=conversation.conversation_id)

@app.get("/conversation/{user_id}/{conversation_id}", response_model=ChatResponse)
def get_conversation(user_id: str, conversation_id: str):
    try:
        conversation = Conversation(user_id, conversation_id)
        messages = conversation.get_messages()
        return {"conversation_id": conversation.conversation_id, "user_id": conversation.user_id, "messages": messages}
    except Exception as exc:
        logger.exception("Failed to retrieve conversation")
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc
    



@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        conversation = Conversation(request.user_id, request.conversation_id)
        conversation.add_message({"role": "Human", "content": request.message})
        reply = run_agent(conversation.get_messages())
        conversation.add_message({"role": "AI", "content": reply})
        return ChatResponse(reply=reply, user_id=request.user_id, conversation_id=request.conversation_id)

    except Exception as exc:
        logger.exception("Agent invocation failed")

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc
