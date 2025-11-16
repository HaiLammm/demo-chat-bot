import config
from utils.logger import setup_logger
from rag.rag_chain import get_rag_chain
from utils.database import save_chat
import re
import time

logger = setup_logger()

# Rate limiting (user_id: [timestamp1, timestamp2, ...])
RATE_LIMIT = {}

def check_rate_limit(user_id, max_requests=5, time_window=60):
    """Check if user exceeds rate limit"""
    now = time.time()
    if user_id not in RATE_LIMIT:
        RATE_LIMIT[user_id] = []

    # Remove old timestamps outside time window
    RATE_LIMIT[user_id] = [t for t in RATE_LIMIT[user_id] if now - t < time_window]

    if len(RATE_LIMIT[user_id]) >= max_requests:
        return False

    RATE_LIMIT[user_id].append(now)
    return True

def sanitize_input(text):
    """Basic input sanitization - remove excessive whitespace, normalize"""
    if not text or not isinstance(text, str):
        return ""
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    return text[:500]  # Limit query length

async def get_rag_response(query):
    """Get RAG response with error handling"""
    try:
        rag_chain = get_rag_chain()  # Create fresh chain per request
        response = rag_chain.invoke({"query": query})["result"]
        return response
    except Exception as e:
        logger.error(f"RAG processing failed: {e}")
        raise RuntimeError("Xin lỗi, tôi không thể xử lý câu hỏi này lúc này.")

async def on_message(message, bot):
    if message.author == bot.user:
        return

    logger.info(f"Received message from {message.author}: {message.content}")

    if bot.user.mentioned_in(message):
        # Check rate limit
        if not check_rate_limit(message.author.id):
            await message.channel.send("Bạn đang gửi quá nhiều tin nhắn. Hãy chờ một chút rồi thử lại!")
            return

        query = message.content.replace(f"<@{bot.user.id}>", "").strip()
        query = sanitize_input(query)

        if not query:
            await message.channel.send("Xin chào! Bạn có thể hỏi tôi bất kỳ câu hỏi nào.")
            return

        try:
            logger.info(f"Processing RAG query from {message.author}: {query}")
            response = await get_rag_response(query)

            # Handle response length
            max_length = 1900  # Discord limit is 2000, leave room for formatting
            if len(response) > max_length:
                response = response[:max_length] + "..."

            await message.channel.send(response)
            save_chat(message.author.id, query, response)

        except RuntimeError as e:
            # User-friendly error message
            await message.channel.send(str(e))
        except Exception as e:
            # Unexpected error - log but don't expose details
            await message.channel.send("Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.")
            logger.error(f"Unexpected error processing message: {e}")

    await bot.process_commands(message)
