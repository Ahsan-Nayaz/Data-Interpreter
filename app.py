import asyncio

__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chainlit as cl
from interpreter.core.core import Interpreter
from dotenv import load_dotenv
import logging
import secrets
from pathlib import Path

load_dotenv(dotenv_path='venv/.env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DELAY = 0.04


@cl.on_chat_start
async def start():
    """
    Start the chat by generating a unique ID and initializing the interpreter.
    If the interpreter is not None, reset it. Otherwise, do nothing.
    Generate a new unique ID if the current unique ID in the user session is the same as the generated one.
    Set the model and context window for the interpreter.
    Read the content of the 'system_message.txt' file and append it to the system message in the interpreter.
    Create an async chain for the interpreter's chat function and store it in the user session.
    Store the unique ID in the user session.
    """
    unique_id = secrets.token_urlsafe(16)
    interpreter = Interpreter()
    if interpreter is not None:
        interpreter.reset()
    else:
        pass
    while cl.user_session.get("unique_id") == unique_id:
        unique_id = secrets.token_urlsafe(16)
    logging.debug(f'Generated unique_id: {unique_id}')

    interpreter.model = "azure/gpt-4-32k-0613"
    interpreter.context_window = 32000

    file_path = Path('prompts/system_message.txt')
    try:
        interpreter.system_message += file_path.read_text().replace('{download}', f'history/{unique_id}/conversations/downloads')
    except FileNotFoundError:
        logging.error("File not found: system_message.txt")
    except Exception as e:
        logging.error(f"Error occurred while reading system_message.txt: {str(e)}")

    llm_chain = cl.make_async(interpreter)
    cl.user_session.set("llm_chain", llm_chain)
    cl.user_session.set("unique_id", unique_id)


@cl.on_message
async def on_message(message: str):
    """
    This function is the event handler for incoming messages. It takes in a message as a parameter and processes it
    using the LLM chain. The function retrieves the LLM chain and unique ID from the user session. It initializes
    empty messages, code, and output objects. It then iterates through the chunks of the LLM chain, processing each
    chunk accordingly. If a chunk indicates the end of a message, code, or execution, the corresponding objects are
    reset. If a chunk contains a message, code, or output, it is streamed to the respective objects. After each
    chunk, the function sleeps for a specified delay. Finally, the function sends the processed messages, code,
    and output. If an error occurs during the execution of the function, it is logged.

    Parameters:
    - message (str): The incoming message to be processed.

    Returns:
    - None
    """
    try:
        llm_chain = cl.user_session.get("llm_chain")
        unique_id = cl.user_session.get("unique_id")
        logger.info(f'Received message: {message}')
        msg = cl.Message(content="")
        out = cl.Message(content="")
        code = cl.Message(content="", language='python')
        for chunk in llm_chain(message, stream=True, display=False, uuid=unique_id):
            logger.info(f'Processing chunk: {chunk}')
            if 'end_of_message' in chunk.keys():
                msg = cl.Message(content="")
            if 'end_of_code' in chunk.keys():
                code = cl.Message(content="", language='python')
            if 'end_of_execution' in chunk.keys():
                out = cl.Message(content="")
                msg = cl.Message(content="")
            if 'message' in chunk.keys():
                await msg.stream_token(token=chunk['message'])
            if 'code' in chunk.keys():
                await code.stream_token(token=chunk['code'])
            if 'output' in chunk.keys():
                await out.stream_token(token=chunk["output"])
            await asyncio.sleep(DELAY)
        await msg.send()
        await out.send()
        await code.send()
    except Exception as e:
        logger.error(f"An error occurred: {type(e).__name__} - {str(e)}")
