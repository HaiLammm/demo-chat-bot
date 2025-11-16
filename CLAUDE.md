# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Bot
```bash
python bot.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Updating Vector Store
```bash
python update_vectorstore.py
```

## Architecture Overview

This is a Discord AI chatbot that integrates Retrieval-Augmented Generation (RAG) for contextual responses. The bot uses Ollama for local LLM inference and ChromaDB for vector storage.

### Core Modules

- **`commands/`**: Discord bot commands organized as cogs
  - `general.py`: Basic user commands (help, ping, stats)
  - `admin.py`: Administrative commands (kick, ban, clear messages) for server management
  - `ai.py`: AI-powered commands that leverage the RAG system for contextual responses
- **`events/`**: Asynchronous event handlers for Discord.py library
  - `on_ready.py`: Bot initialization and status logging when connected to Discord
  - `on_message.py`: Main message processing handler that routes queries to the RAG system
  - `on_member_join.py`: Welcome message system using configured channel ID
- **`rag/`**: Complete RAG implementation using LangChain framework
  - `data_loader.py`: Document loading and text chunking utilities with preprocessing
  - `embeddings.py`: Vector embedding generation and management using sentence transformers
  - `rag_chain.py`: LangChain pipeline setup, vectorstore integration, and prompt engineering
  - `vectorstore/`: ChromaDB storage directory with persistence and indexing
- **`utils/`**: Shared utility functions and helpers
  - Logging configuration and formatted output to `logs/bot.log`
  - Database operations using SQLite for user data and conversation history
  - API wrappers for external services and error handling utilities
- **`data/`**: Static knowledge base and configuration files
  - `knowledge.txt`: Primary knowledge base document for RAG system
  - Additional documentation files for domain-specific context

### Configuration

Requires `.env` file with:
- `DISCORD_TOKEN`: Discord bot token
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model name (default: phi3:latest)
- `WELCOME_CHANNEL_ID`: Discord channel ID for welcome messages

### Data Flow

1. **Knowledge Base Initialization**: Knowledge documents in `data/knowledge.txt` are loaded and processed using the `data_loader.py` module, which handles text chunking with configurable chunk sizes, overlap settings, and preprocessing steps
2. **Embedding Generation**: Text chunks are converted to high-dimensional vector embeddings using sentence transformer models (e.g., all-MiniLM-L6-v2) through the `embeddings.py` module, enabling semantic similarity comparisons
3. **Vector Storage**: Generated embeddings are stored in ChromaDB vectorstore with persistent storage, metadata indexing, and efficient nearest-neighbor search capabilities for scalable retrieval
4. **Query Processing**: When a user sends a message, Discord event handlers in `events/on_message.py` capture the message and determine if it requires AI processing based on command prefixes or keywords
5. **Semantic Search**: The user query is embedded using the same sentence transformer model and used to perform k-nearest neighbor search against the stored vectors using cosine similarity scoring
6. **Context Retrieval**: Top-k most semantically similar document chunks are retrieved from the vectorstore, providing relevant context while filtering out irrelevant content
7. **Response Generation**: Retrieved context chunks are fed into a LangChain RAG chain that combines them with a carefully engineered prompt template and sends them to the Ollama LLM for contextual response generation
8. **Response Delivery**: The generated response is sent back through Discord's API, and conversation context may be stored in the SQLite database for future reference or continuity

### Activity Stream: `!chat Giải thích cách cài đặt Linux Mint`

When a user sends `!chat Giải thích cách cài đặt Linux Mint`, here's the detailed activity stream showing how each module works:

#### **Step 1: Command Detection** (`commands/ai.py:11-18`)
- Discord detects the `!chat` command prefix
- `ai.py` cog intercepts the command via `@commands.command(name='chat')`
- The command handler extracts the query: `"Giải thích cách cài đặt Linux Mint"`
- Rate limiting is not applied for command-based queries (only for mentions)

#### **Step 2: RAG Chain Initialization** (`rag/rag_chain.py:7-25`)
- `get_rag_chain()` function creates a fresh chain per request
- Initializes **ChatOllama** with configured model (e.g., `phi3:latest`)
- Creates Chroma vectorstore retriever with `k=1` (top 1 most relevant document)
- Uses Vietnamese prompt template for contextual responses
- Returns `RetrievalQA` chain combining LLM with vector retrieval

#### **Step 3: Vector Search** (`rag/vectorstore.py:10-15`)
- Vectorstore retrieves from ChromaDB at `rag/vectorstore/`
- Uses embedding model (Ollama or HuggingFace fallback) to process query
- Performs cosine similarity search against stored document embeddings
- Returns the most relevant text chunk from knowledge base

#### **Step 4: Context Enhancement** (`rag/rag_chain.py:12-18`)
- LangChain combines retrieved context with user query
- Applies Vietnamese prompt template: `"Sử dụng thông tin sau để trả lời câu hỏi một cách ngắn gọn. Nếu không biết, nói 'Tôi không biết.'"`
- Formats input as: `{"context": [relevant_text], "question": "Giải thích cách cài đặt Linux Mint"}`

#### **Step 5: LLM Inference** (`rag/rag_chain.py:8`)
- Ollama processes the enhanced prompt locally
- Timeout: 300 seconds with 4 threads for optimal performance
- LLM generates response based on retrieved context + general knowledge
- Returns structured result with `result` field containing the answer

#### **Step 6: Response Processing** (`commands/ai.py:14-18`)
- Response length validation (1900 character limit for Discord)
- Error handling with user-friendly Vietnamese error messages
- Response is sent back to the Discord channel
- Conversation history is saved to SQLite database via `utils/database.py`

#### **Step 7: Logging & Monitoring** (`events/on_message.py:50,66`)
- All interactions are logged to `logs/bot.log`
- Query/response pairs are tracked for debugging and analytics
- Success/failure status is recorded for system health monitoring

### Alternative Flow: Bot Mention Processing

If user sends `@bot Giải thích cách cài đặt Linux Mint` instead of `!chat`:

#### **Step 1: Mention Detection** (`events/on_message.py:52`)
- Bot detects when user mentions the bot with `@bot`
- Rate limiting check prevents spam (max 5 requests per 60 seconds)
- Extracts clean query by removing bot mention

#### **Step 2: Query Sanitization** (`events/on_message.py:28-34`)
- `sanitize_input()` function cleans the query
- Removes excessive whitespace and normalizes text
- Limits query length to 500 characters
- Returns: `"Giải thích cách cài đặt Linux Mint"`

#### **Step 3: RAG Response Generation** (`events/on_message.py:36-44`)
- `get_rag_response()` function handles the complete RAG pipeline
- Error handling with Vietnamese fallback messages
- Same RAG chain processing as command-based flow
- Returns AI-generated response

#### **Step 4: Response Delivery** (`events/on_message.py:69-75`)
- Response length validation and truncation if needed
- Direct message reply to the user's channel
- Database storage for conversation continuity
- Graceful error handling for various failure scenarios