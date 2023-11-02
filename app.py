import asyncio

__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chainlit as cl
import interpreter
from dotenv import load_dotenv
import logging
import secrets
from pathlib import Path

load_dotenv(dotenv_path='venv/.env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DELAY = 0.06
"""
This code defines a function called 'main' that is executed when a chat starts. The function generates a unique ID 
using the 'secrets' module and ensures that the generated ID is not already stored in the user session. It then logs 
the generated unique ID.

The code sets the model and context window for an interpreter object. It also reads the contents of a file called 
'system_message.txt' and adds it to the system message of the interpreter. If the file is not found or if any other 
exception occurs, appropriate error messages are logged.

The code retrieves the chat function from the interpreter and stores it in a variable called 'llm_chain'. The 
generated unique ID and 'llm_chain' are then stored in the user session.

Summary: This code sets up a chat functionality by generating a unique ID, configuring the interpreter, and handling 
system messages. It also stores relevant information in the user session.
"""


@cl.on_chat_start
async def main():
    unique_id = secrets.token_urlsafe(16)
    if interpreter is not None:
        interpreter.reset()
    else:
        pass
    while cl.user_session.get("unique_id") == unique_id:
        unique_id = secrets.token_urlsafe(16)
    logging.debug(f'Generated unique_id: {unique_id}')

    interpreter.model = "azure/gpt-4-32k-0613"
    interpreter.context_window = 32000

    file_path = Path('system_message.txt')
    try:
        interpreter.system_message += file_path.read_text()
    except FileNotFoundError:
        logging.error("File not found: system_message.txt")
    except Exception as e:
        logging.error(f"Error occurred while reading system_message.txt: {str(e)}")

    llm_chain = interpreter.chat
    cl.user_session.set("llm_chain", llm_chain)
    cl.user_session.set("unique_id", unique_id)




"""

This is a function named 'main' which takes a string parameter 'message' and runs on every message. It performs the following tasks:
1. Checks if the 'message' parameter is a string, otherwise raises a ValueError.
2. Retrieves values from the user session for 'llm_chain' and 'unique_id'.
3. Logs the 'message' parameter.
4. Initializes three instances of the 'cl.Message' class named 'msg', 'out', and 'code'.
5. Iterates over the chunks returned by the 'llm_chain' function.
6. Checks for specific keys in each chunk and performs corresponding actions:
   - If 'end_of_message' key is present, resets the 'msg' instance.
   - If 'end_of_code' key is present, resets the 'code' instance.
   - If 'end_of_execution' key is present, resets both 'out' and 'msg' instances.
   - If 'message' key is present, streams the token to 'msg'.
   - If 'code' key is present, streams the token to 'code'.
   - If 'output' key is present, streams the token to 'out'.
   - Sleeps for 0.06 seconds.
7. Sends the 'msg', 'out', and 'code' instances.
8. Handles any exceptions that occur and logs the error.

"""


@cl.on_message
async def main(message: str):
    try:
        llm_chain = cl.user_session.get("llm_chain")
        unique_id = cl.user_session.get("unique_id")
        logger.info(f'Received message: {message}')
        msg = cl.Message(content="")
        out = cl.Message(content="")
        code = cl.Message(content="", language='python')
        for chunk in await llm_chain(message, stream=True, display=False, uuid=unique_id):
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
