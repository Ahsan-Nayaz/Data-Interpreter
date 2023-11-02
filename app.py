from pathlib import Path
import asyncio
import logging
import secrets

__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chainlit as cl
import interpreter
from dotenv import load_dotenv

load_dotenv(dotenv_path='venv/.env')
logging.basicConfig(level=logging.INFO)


@cl.on_chat_start
async def main():
    unique_id = secrets.token_urlsafe(16)
    while cl.user_session.get("unique_id") == unique_id:
        unique_id = secrets.token_urlsafe(16)
    logging.info(f'Generated unique_id: {unique_id}')

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


logger = logging.getLogger(__name__)


@cl.on_message
async def main(message: str):
    try:
        if not isinstance(message, str):
            raise ValueError("message parameter must be a string")
        
        llm_chain = cl.user_session.get("llm_chain")
        unique_id = cl.user_session.get("unique_id")
        logger.info(message)
        msg = cl.Message(content="")
        out = cl.Message(content="")
        code = cl.Message(content="", language='python')
        for chunk in await llm_chain(message, stream=True, display=False, uuid=unique_id):
            logger.info(chunk)
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
            await asyncio.sleep(0.06)
        await msg.send()
        await out.send()
        await code.send()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
