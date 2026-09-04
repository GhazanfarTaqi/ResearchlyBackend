# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field
# import logging
# from main_agent import run_agent


# logging.basicConfig(level=logging.INFO)

# app = FastAPI(title="Chatbot API", version="1.0.0")

# logger = logging.getLogger(__name__)

# # Adjust for your actual frontend origin(s) in production
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # ---------------------------------------------------------------------------
# # Schemas
# # ---------------------------------------------------------------------------
# class ChatRequest(BaseModel):
#     message: str = Field(..., min_length=1, description="User's message")


# class ChatResponse(BaseModel):
#     reply: str


# # ---------------------------------------------------------------------------
# # Routes
# # ---------------------------------------------------------------------------
# @app.get("/health")
# def health():
#     return {"status": "ok"}


# @app.post("/chat", response_model=ChatResponse)
# def chat(request: ChatRequest):
#     try:
#         reply = run_agent(request.message)
#         return ChatResponse(reply=reply)
#     except Exception as exc:
#         logger.exception("Agent invocation failed")
#         raise HTTPException(status_code=500, detail=str(exc)) from exc

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from main_agent import run_agent


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        # Add Vercel URL after deploying frontend
        # "https://researchly.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        reply = run_agent(request.message)

        return ChatResponse(reply=reply)

    except Exception as exc:
        logger.exception("Agent invocation failed")

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc