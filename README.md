# Researchly backend workflow

This document maps the current application workflow, with emphasis on the AI
execution path. It describes the code as it exists today; the "implemented"
and "not connected" notes are intentional so that the architecture is not
mistaken for a fully integrated pipeline.

## System overview

```text
Next.js browser UI
        |
        | POST /chat { "message": "..." }
        v
FastAPI (main.py)
        |
        v
LangGraph supervisor (main_agent.py)
        |
        +--> RAG tool --> Chroma retriever --> Mistral answer
        |
        +--> Research tool --> OpenAlex papers --> Groq synthesis
        |
        v
Final text response
        |
        v
Browser renders Markdown and keeps only local IDs in localStorage
```

The backend is a synchronous FastAPI service. A request stays open while the
supervisor and any selected model/tool calls complete; there is no streaming
or job queue. Conversations are persisted in MongoDB, but there is no
authentication or multi-conversation listing endpoint.

## Clerk authentication in the frontend

The Next.js frontend uses Clerk to authenticate users. Clerk middleware
protects application routes, while authenticated server actions resolve the
current Clerk `userId` on the server:

* `createConversation()` passes the Clerk user ID to `POST /conversation`.
* `getConversation()` passes the Clerk user ID to
  `GET /conversation/{user_id}/{conversation_id}`.
* `sendMessage()` passes the Clerk user ID and conversation ID to `POST /chat`.

The browser does not create or submit a random user ID. Local storage stores
only the current conversation ID, namespaced by the Clerk user ID.

## Repository map

| Area | Responsibility |
| --- | --- |
| `main.py` | FastAPI app, CORS, request/response validation, `/health`, `/chat`, `/conversation` |
| `main_agent.py` | Live LangGraph supervisor and tool routing |
| `agents/research_agent.py` | External-paper research graph |
| `agents/rag_agent.py` | Retrieval-grounded answer generation |
| `vector_db.py` | Chroma persistence, Hugging Face embeddings, MMR retriever |
| `tool/research_tool.py` | OpenAlex paper search and abstract reconstruction |
| `tool/scrap_tool.py` | DOI metadata lookup and legal open-access PDF download |
| `agents/writer_agent.py` | PDF ingestion, notes, and starter-manuscript graph; currently not wired into the live supervisor |
| `db.py`, `database/` | MongoDB paper persistence helpers; used by the writer graph |
| `chroma_langchain_db/` | Local Chroma data directory created at runtime (ignored by Git) |

## End-to-end user request

1. The user enters text in `frontend/components/ChatInput.js` or chooses a
   suggestion in `frontend/components/WelcomeScreen.js`.
2. `frontend/app/page.js` immediately adds the user message to the UI, disables
   the input, and calls `frontend/lib/api.js`.
3. The frontend sends:

   ```http
   POST http://127.0.0.1:8000/chat
   Content-Type: application/json

   {
     "message": "...",
     "user_id": "...",
     "conversation_id": "..."
   }
   ```

   `NEXT_PUBLIC_API_URL` can replace the default API origin.
4. FastAPI validates the body with `ChatRequest`, loads or creates the
   `Conversation`, appends the human message, and calls
   `run_agent(conversation.get_messages())`.
5. The supervisor returns the last LangGraph message as `ChatResponse.reply`.
6. The backend appends the AI message to MongoDB. The frontend appends the
   assistant response to the current UI, renders it as Markdown, and persists
   only local identifiers for the user and current conversation.
7. On a server-side error, FastAPI logs the exception and returns HTTP 500 with
   `detail`; the frontend displays that detail as an assistant error message.

## Conversation and memory endpoints

### Create a conversation

```http
POST /conversation
Content-Type: application/json

{"user_id":"..."}
```

The response is:

```json
{
  "reply": "Conversation started",
  "user_id": "...",
  "conversation_id": "..."
}
```

### Restore a conversation

```http
GET /conversation/{user_id}/{conversation_id}
```

The response contains the user ID, conversation ID, and the stored
`{"role":"Human"|"AI","content":"..."}` message array. Unknown conversations
return HTTP 404.

### Send a message

```http
POST /chat
Content-Type: application/json

{
  "message": "...",
  "user_id": "...",
  "conversation_id": "..."
}
```

The response contains `reply`, `user_id`, and `conversation_id`. The conversation
is loaded from MongoDB for every request, so prior Human/AI messages are sent
as agent context.

### List conversations

```http
GET /conversations/{user_id}
```

The response contains a `conversations` array sorted by newest update:

```json
{
  "user_id": "...",
  "conversations": [
    {
      "conversation_id": "...",
      "title": "Retrieval Augmented Generation",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

Titles are derived from the first Human message and truncated for sidebar display.

## Live AI supervisor workflow

`main_agent.py` builds this graph:

```text
START
  |
  v
model (Groq: openai/gpt-oss-120b)
  |
  +-- no tool call --> END --> final response
  |
  +-- tool call -----> tools
                         |
                         v
                       model
```

The supervisor state contains an append-only `messages` list. The initial
message is a `HumanMessage` containing the user's query. The Groq model is
bound to two tools:

### `rag_search(query)`

Use this route when the answer should come from documents already indexed in
the local vector database.

1. `agents/rag_agent.py` invokes the Chroma retriever with the query.
2. Chroma uses MMR with `fetch_k=10`, returns `k=4`, and
   `lambda_mult=0.5`.
3. The retrieved page contents are joined into a context string. Current RAG
   prompting does not include document metadata in that string.
4. `ChatMistralAI(model="mistral-small-2506")` receives the query and context.
5. The prompt requires a JSON-shaped answer with `answer` and
   `insufficient_context`, but the result is returned as the model response
   object rather than parsed/validated JSON.
6. The tool result is added to the supervisor message history.
7. The supervisor sees the tool result and generates the final user-facing
   response.

The vector store is initialized when `vector_db.py` is imported:

```text
HuggingFaceEndpointEmbeddings
  model: sentence-transformers/all-MiniLM-L6-v2
        |
        v
Chroma("./chroma_langchain_db")
```

### `research_topic(topic)`

Use this route when the model decides that new external academic sources are
needed.

1. `agents/research_agent.py` starts a LangGraph with state fields for
   `topic`, `papers`, `messages`, and `report`.
2. `get_papers` calls `tool/research_tool.py`.
3. The tool calls OpenAlex with the topic, requests five results ordered by
   relevance, and maps each result to title, year, citation count, DOI, URL,
   and reconstructed abstract.
4. `research` sends the topic and paper records to
   `ChatGroq(model="openai/gpt-oss-20b", temperature=0.7)`.
5. The research prompt asks for key findings, methods, agreement, conflicts,
   gaps, conclusion, and a paper list. It explicitly tells the model not to
   invent sources and to cite claims using paper titles.
6. The resulting `report` is returned to the supervisor as the tool result.
7. The supervisor can stop or call another tool before producing the final
   response.

## PDF ingestion and writer workflow

`agents/writer_agent.py` contains a separate, more complete graph. It is not
currently reachable from the live `tools` list in `main_agent.py`; the
`write_document` tool is defined as a placeholder and is also omitted from
that list.

When invoked directly with a state containing `topic` and `papers`, its graph
is:

```text
START
  |
  v
scrapePapers
  |
  v
makeChunks
  |
  v
makeNotes
  |
  v
makeStaterTempelate
  |
  v
END
```

### `scrapePapers`

For each paper DOI, `tool/scrap_tool.py`:

1. Resolves metadata through Crossref.
2. Searches Unpaywall for an open-access location.
3. Falls back to an arXiv title search.
4. Downloads a PDF only when a legal PDF URL is found.
5. Records metadata, PDF URL, local path, source, and status.

Paywalled papers are not bypassed; their metadata and publisher URL are
retained instead.

### `makeChunks`

For downloaded PDFs, the writer:

1. Loads pages with `PyPDFLoader`.
2. Splits text with `RecursiveCharacterTextSplitter`
   (`chunk_size=1000`, `chunk_overlap=200`).
3. Checks MongoDB by DOI.
4. For a new DOI, inserts the paper into MongoDB and adds chunks to Chroma.
5. Keeps paper metadata and chunks in graph state.

If no PDF is available, the abstract is retained as a single fallback
"chunk". This fallback is used for writer notes, not automatically inserted
into Chroma.

### `makeNotes`

Each chunk is sent to `notes_agent` (`ChatMistralAI`, `codestral-latest`) for
paper-specific extraction. The per-chunk notes are then synthesized into one
structured research note per paper.

### `makeStaterTempelate`

The final notes, topic, and references are sent to the same notes model to
produce a starter manuscript. The prompts request academic structure,
evidence-backed writing, and placeholders for information that is not
available. The result is stored as `starter_manuscript`.

## Persistence and data stores

There are currently three separate persistence concerns:

* **Browser:** user and current conversation IDs in `localStorage`. Chat
  messages are loaded from the backend and are not persisted in the browser.
* **MongoDB conversations:** Human and AI messages are stored in the
  `conversations` collection. The live `/chat` route appends both messages
  for its memory context.
* **Chroma:** local vector index in `backend/chroma_langchain_db`, populated
  by the writer graph when PDF chunks are added.
* **MongoDB papers:** paper metadata in the database returned by
  `database/connection.py`; `db.py` provides DOI lookup and insertion helpers.

The live `/chat` route writes conversation messages to MongoDB, but it does not
persist research reports or tool traces separately.

## Configuration

The backend loads `.env` through `python-dotenv`. The code expects:

| Variable | Used by |
| --- | --- |
| `GROQ_API_KEY` | Groq supervisor and research model |
| `MISTRAL_API_KEY` | RAG and writer/notes models |
| `HF_TOKEN` | Hugging Face endpoint embeddings |
| `OPENALEX_API_KEY` | OpenAlex research search |
| `MONGODB_URI` | MongoDB paper helpers |
| `EMAIL` | Unpaywall request identity in the PDF workflow |
| `NEXT_PUBLIC_API_URL` | Frontend only; overrides the backend URL |
| `BACKEND_API_URL` | Server-action-only backend URL; recommended in deployed Next.js |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk browser publishable key |
| `CLERK_SECRET_KEY` | Clerk server secret key |

## MongoDB troubleshooting

Conversation endpoints require `MONGODB_URI` in `backend/.env` or the backend
process environment. A valid MongoDB Atlas URI typically starts with
`mongodb+srv://`.

If `/conversation` or `/chat` returns HTTP 503:

1. Confirm `MONGODB_URI` is set and points to an active cluster.
2. Confirm the Atlas cluster hostname still exists and DNS resolves.
3. Confirm the database user is active and its password is URL-encoded.
4. Confirm the local or deployment network is allowed in Atlas Network Access.
5. Restart the backend after changing `.env`.

`GET /health` reports `database: "connected"` or `"disconnected"` and does not
expose credentials or the MongoDB URI.

## Production deployment

### Backend

Set all backend variables from `backend/.env.example` in the hosting provider:

```powershell
cd backend
uv sync --locked
uv run uvicorn main:app --host 0.0.0.0 --port $env:PORT
```

Required production values:

* `MONGODB_URI`
* `INTERNAL_API_KEY`
* `CORS_ALLOWED_ORIGINS`
* Provider keys used by the enabled agent features

Use HTTPS and restrict `CORS_ALLOWED_ORIGINS` to the deployed frontend origin.
The backend health route is public; conversation and chat routes require the
shared `X-Internal-API-Key` header.

### Frontend

Set all frontend variables from `frontend/.env.example` in Vercel or another
Next.js host:

* `BACKEND_API_URL`
* `INTERNAL_API_KEY`
* `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
* `CLERK_SECRET_KEY`

`INTERNAL_API_KEY` must have the exact same value in Next.js and FastAPI.
Deploy Clerk as a production instance and configure its permitted origins and
redirect URLs for the production domain.

Before production launch:

1. Rotate every provider/API key that was previously committed or shared.
2. Replace MongoDB, Clerk, Mistral, OpenAlex, Hugging Face, Groq, and OpenAI
   credentials if they exist in screenshots, logs, chats, or source history.
3. Restrict MongoDB Atlas Network Access and database-user permissions.
4. Set production Clerk keys rather than development keys.
5. Configure monitoring and provider usage limits.

Provider libraries normally read their API keys from their standard
environment-variable names. Never commit `.env` or downloaded papers; both
are ignored by the backend Git configuration.

## Running locally

From `backend`:

```powershell
uv sync
uv run uvicorn main:app --reload
```

From `frontend`:

```powershell
npm install
npm run dev
```

Useful smoke checks:

```http
GET http://127.0.0.1:8000/health

POST http://127.0.0.1:8000/chat
{"message":"Research recent developments in retrieval augmented generation."}
```

## Current integration boundaries

* Only `rag_search` and `research_topic` are available to the live supervisor.
* The writer graph must be invoked separately; it is not a follow-up stage of
  a chat request.
* There is no implemented document-upload/indexing API. Chroma population is
  coupled to the dormant writer graph.
* `write_document` is a placeholder and should not be treated as a working
  production tool.
* `agents.py` is an old commented example and is not part of the FastAPI
  request path.
* Error handling in the RAG and vector-store helpers currently prints and
  returns `None`; callers should not assume a structured error response.