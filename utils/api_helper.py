import ollama
import asyncio

async def test_ollama_connection():
    """
    Tests the connection to Ollama by pulling a model.
    """
    try:
        await asyncio.to_thread(ollama.pull, "llama3")
        return True, "Successfully connected to Ollama and pulled the model."
    except Exception as e:
        return False, f"Failed to connect to Ollama: {e}"

async def send_long_message(ctx, message):
    """
    Sends a long message by splitting it into chunks of 1900 characters.
    Tries to split at word boundaries to avoid cutting words in half.
    """
    max_length = 1900  # Discord limit is 2000, leave buffer

    if len(message) <= max_length:
        await ctx.send(message)
        return

    # Split message into chunks, trying to respect word boundaries
    chunks = []
    current_chunk = ""

    for line in message.split('\n'):
        # If adding this line would exceed limit
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                # Line itself is too long, force split
                while len(line) > max_length:
                    chunks.append(line[:max_length])
                    line = line[max_length:]
                current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Send all chunks
    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            await ctx.send(chunk)
        else:
            await ctx.send(chunk + " *(tiếp theo)...")