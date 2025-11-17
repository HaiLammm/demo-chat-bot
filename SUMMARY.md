# Project Summary: Discord RAG Chat Bot

This project is a Discord chatbot that uses a Retrieval-Augmented Generation (RAG) architecture to answer questions. It's designed to be self-contained, running a local Large Language Model (LLM) with Ollama and using a local vector database (ChromaDB) for its knowledge base.

## How It Works

1.  **Knowledge Base:** The bot's knowledge is stored in `data/knowledge.txt`.
2.  **Vector Store:** The `update_vectorstore.py` script processes the knowledge base, creates vector embeddings using Sentence Transformers, and stores them in a ChromaDB database.
3.  **Discord Bot:** The main application is a Python-based Discord bot (`bot.py`) that listens for commands and messages.
4.  **RAG Chain:** When a user asks a question with the `!chat` command or by mentioning the bot, the query is sent to a RAG chain built with LangChain.
5.  **Response Generation:** The RAG chain retrieves the most relevant information from the vector store, combines it with the user's question in a prompt, and sends it to the locally hosted LLM via Ollama to generate a context-aware answer.
6.  **Interaction:** The bot then sends the LLM's response back to the Discord channel.

## Project Structure

The project is structured into several modules:

*   `commands/`: Contains the bot's command handlers (e.g., `ai.py` for the `!chat` command).
*   `rag/`:  Manages the RAG pipeline, including data loading, embeddings, the vector store, and the RAG chain itself.
*   `events/`: Handles Discord events like new members joining or new messages.
*   `utils/`: Provides utility functions for logging and database interactions.
*   `config.py`: Centralizes all configuration settings.

In short, this is a powerful, private, and customizable AI chatbot for Discord that can answer questions based on a provided knowledge base.

## Detailed Functionality

### `bot.py` (Main Bot Entry Point)
*   `on_command_error(ctx, error)`: An asynchronous event handler that catches and processes errors occurring during command execution. It specifically logs HTTP errors.
*   `on_ready()`: An asynchronous event handler that is called when the bot successfully connects to Discord. It delegates to `events.on_ready.on_ready`.
*   `on_message(message)`: An asynchronous event handler that is called every time a message is sent in a channel the bot has access to. It delegates to `events.on_message.on_message`.
*   `on_member_join(member)`: An asynchronous event handler that is called when a new member joins the Discord server. It delegates to `events.on_member_join.on_member_join`.
*   `main()`: The main asynchronous function that sets up the bot, loads commands, and starts the bot's connection to Discord.

### `commands/admin.py` (Admin Commands)
*   `clear(self, ctx, amount: int = 5)`: A command that allows users with `manage_messages` permission to delete a specified number of messages from the channel.
*   `clear_error(self, ctx, error)`: Error handler for the `clear` command, specifically catching `MissingPermissions` errors.
*   `ban(self, ctx, member: discord.Member, *, reason="Không có lý do")`: A command that allows users with `ban_members` permission to ban a member from the server with an optional reason.
*   `ban_error(self, ctx, error)`: Error handler for the `ban` command, specifically catching `MissingPermissions` errors.
*   `kick(self, ctx, member: discord.Member, *, reason="Không có lý do")`: A command that allows users with `kick_members` permission to kick a member from the server with an optional reason.
*   `kick_error(self, ctx, error)`: Error handler for the `kick` command, specifically catching `MissingPermissions` errors.
*   `setup(bot)`: An asynchronous function to add the `Admin` cog to the bot.

### `commands/ai.py` (AI Chat Command)
*   `__init__(self, bot)`: Initializes the AI cog, setting up the bot instance and the RAG chain.
*   `chat(self, ctx, *, query: str)`: A command that processes a user's query using the RAG chain, sends the response to Discord, and saves the chat history.
*   `setup(bot)`: An asynchronous function to add the `AI` cog to the bot.

### `commands/general.py` (General Commands)
*   `ping(self, ctx)`: A command that responds with the bot's latency to Discord.
*   `info(self, ctx)`: A command that displays an embedded message with information about the bot.
*   `setup(bot)`: An asynchronous function to add the `General` cog to the bot.

### `events/on_member_join.py` (Member Join Event Handler)
*   `on_member_join(member, bot)`: An asynchronous function that sends a welcome message to a predefined channel when a new member joins the server.

### `events/on_message.py` (Message Event Handler)
*   `check_rate_limit(user_id, max_requests=5, time_window=60)`: Checks if a user has exceeded the rate limit for sending messages to the bot.
*   `sanitize_input(text)`: Cleans and sanitizes user input by removing excessive whitespace and limiting query length.
*   `get_rag_response(query)`: Retrieves a response from the RAG chain, including error handling.
*   `on_message(message, bot)`: An asynchronous function that processes incoming messages, handles bot mentions, applies rate limiting, sanitizes input, and generates RAG responses.

### `events/on_ready.py` (Bot Ready Event Handler)
*   `on_ready(bot)`: An asynchronous function that is called when the bot is ready. It logs the bot's status, tests Ollama connection, and initializes or updates the RAG vector store.

### `rag/data_loader.py` (Data Loading for RAG)
*   `load_data(file_path='data/knowledge.txt')`: Loads text data from a specified file, splits it into chunks, and returns a list of documents.

### `rag/embeddings.py` (Embedding Generation)
*   `get_embeddings()`: Returns an embedding model, preferring OllamaEmbeddings if available, otherwise falling back to HuggingFaceEmbeddings.

### `rag/rag_chain.py` (RAG Chain Construction)
*   `get_rag_chain()`: Constructs and returns a LangChain RAG chain, integrating the Ollama LLM, vector store retriever, and a prompt template for contextual question answering.

### `rag/vectorstore.py` (Vector Store Management)
*   `get_vectorstore()`: Initializes and returns a Chroma vector store with the configured embeddings and persistence directory.
*   `update_vectorstore()`: Clears the existing vector store, loads data from `knowledge.txt`, generates embeddings, and populates a new Chroma vector store.

### `update_vectorstore.py` (Script to Update Vector Store)
*   `if __name__ == "__main__":`: The main execution block for the script, which calls `rag.vectorstore.update_vectorstore()` to refresh the knowledge base in the vector store.

### `utils/api_helper.py` (API Utility)
*   `test_ollama_connection()`: Checks the connectivity to the configured Ollama host.

### `utils/database.py` (Database Utilities)
*   `init_db()`: Initializes the SQLite database and creates the `chat_history` table if it doesn't exist.
*   `save_chat(user_id, query, response)`: Saves a user's chat interaction (user ID, query, and bot response) to the SQLite database.

### `utils/logger.py` (Logging Utility)
*   `setup_logger()`: Configures and returns a logger instance, ensuring logs are written to `logs/bot.log`.
