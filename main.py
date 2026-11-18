import logging
import os
from pymongo.errors import ConfigurationError, PyMongoError

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from models.Conversation import Conversation
from agents.main_agent import run_agent


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly API",
    version="1.0.0"
)

configured_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in configured_origins
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    user_id: str = Field(..., min_length=1)
    conversation_id: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str 
    user_id: str 
    conversation_id: str

class CreateConversationRequest(BaseModel):
    user_id: str = Field(..., min_length=1)

class ConversationResponse(BaseModel):
    reply: str
    user_id: str
    conversation_id: str

class ConversationMessagesResponse(BaseModel):
    user_id: str
    conversation_id: str
    messages: list[dict]

class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None

class ConversationListResponse(BaseModel):
    user_id: str
    conversations: list[ConversationSummary]

def require_internal_api(x_internal_api_key: str | None = Header(default=None)):
    expected_key = os.getenv("INTERNAL_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Backend is not configured.",
        )
    if x_internal_api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized.",
        )


@app.get("/health")
def health():
    try:
        from database.connection import connectdb

        connectdb("admin").admin.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return {"status": "degraded", "database": "disconnected"}

@app.post("/conversation", response_model=ConversationResponse)
def conversation(
    request: CreateConversationRequest,
    x_internal_api_key: str | None = Header(default=None),
):
    require_internal_api(x_internal_api_key)
    try:
        conversation = Conversation(request.user_id)
        return ChatResponse(reply="Conversation started", user_id=request.user_id, conversation_id=conversation.conversation_id)
    except (RuntimeError, ConfigurationError, PyMongoError) as exc:
        logger.exception("Conversation storage unavailable")
        raise HTTPException(
            status_code=503,
            detail="Conversation storage is unavailable. Check MONGODB_URI."
        ) from exc

@app.get("/conversations/{user_id}", response_model=ConversationListResponse)
def list_conversations(
    user_id: str,
    x_internal_api_key: str | None = Header(default=None),
):
    require_internal_api(x_internal_api_key)
    try:
        from database.db_conv_methods import list_conversations as get_conversation_list

        items = get_conversation_list(user_id)
        summaries = []

        for item in items:
            messages = item.get("messages", [])
            first_human = next(
                (
                    message.get("content", "")
                    for message in messages
                    if str(message.get("role", "")).lower() in ("human", "user")
                ),
                "",
            )
            title = first_human.strip().replace("\n", " ")[:48] or "New research"

            summaries.append(
                ConversationSummary(
                    conversation_id=item["conversation_id"],
                    title=title,
                    created_at=item.get("created_at").isoformat()
                    if item.get("created_at") else None,
                    updated_at=item.get("updated_at").isoformat()
                    if item.get("updated_at") else None,
                )
            )

        return {"user_id": user_id, "conversations": summaries}
    except (RuntimeError, ConfigurationError, PyMongoError) as exc:
        logger.exception("Conversation storage unavailable")
        raise HTTPException(
            status_code=503,
            detail="Conversation storage is unavailable. Check MONGODB_URI."
        ) from exc

@app.get("/conversation/{user_id}/{conversation_id}", response_model=ConversationMessagesResponse)
def get_conversation(
    user_id: str,
    conversation_id: str,
    x_internal_api_key: str | None = Header(default=None),
):
    require_internal_api(x_internal_api_key)
    try:
        conversation = Conversation(user_id, conversation_id)
        messages = conversation.get_messages()
        return {"conversation_id": conversation.conversation_id, "user_id": conversation.user_id, "messages": messages}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ConfigurationError, PyMongoError) as exc:
        logger.exception("Conversation storage unavailable")
        raise HTTPException(
            status_code=503,
            detail="Conversation storage is unavailable. Check MONGODB_URI."
        ) from exc
    except Exception as exc:
        logger.exception("Failed to retrieve conversation")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve the conversation."
        ) from exc
    



@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    x_internal_api_key: str | None = Header(default=None),
):
    require_internal_api(x_internal_api_key)
    try:
        conversation = Conversation(request.user_id, request.conversation_id)
        conversation.add_message({"role": "Human", "content": request.message})
        reply = run_agent(conversation.get_messages())
        conversation.add_message({"role": "AI", "content": reply})
        return ChatResponse(reply=reply, user_id=request.user_id, conversation_id=request.conversation_id)

    except (RuntimeError, ConfigurationError, PyMongoError) as exc:
        logger.exception("Conversation storage unavailable")
        raise HTTPException(
            status_code=503,
            detail="Conversation storage is unavailable. Check MONGODB_URI."
        ) from exc
    except Exception as exc:
        logger.exception("Agent invocation failed")

        raise HTTPException(
            status_code=500,
            detail="The research agent could not complete the request."
        ) from exc

