import secrets
import asyncio
import logging

__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chainlit as cl
import interpreter
import os
import shutil
import time
import pandas as pd
import uuid
from dotenv import load_dotenv

load_dotenv(dotenv_path='venv/.env')


@cl.on_chat_start
async def main():
    unique_id = secrets.token_hex(16)
    logging.info(f'Generated unique_id: {unique_id}')

    interpreter.model = "azure/gpt-4-32k-0613"
    interpreter.context_window = 32000

    with open('system_message.txt', 'r') as file:
        interpreter.system_message += file.read()

    llm_chain = interpreter.chat
    cl.user_session.set("llm_chain", llm_chain)
    cl.user_session.set("unique_id", unique_id)


logger = logging.getLogger(__name__)


@cl.on_message
async def main(message: str):
    # Retrieve the chain from the user session

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
        # if 'end_of_' in chunk.keys():
        #     msg = cl.Message(content="")
        if 'message' in chunk.keys():
            await msg.stream_token(token=chunk['message'])
        if 'code' in chunk.keys():
            # msg.language = chunk["executing"]["language"]
            # await msg.stream_token(token=chunk["executing"]['code'])
            await code.stream_token(token=chunk['code'])
        if 'output' in chunk.keys():
            await out.stream_token(token=chunk["output"])
        await asyncio.sleep(0.06)
        # msg.language = ''
        # await chat_output(msg, chunk)
        # await asyncio.sleep(0.06)
    await msg.send()
    await out.send()
    await code.send()
    # Do any post-processing here


#  directory_path = f"data/graph/"
#   print(directory_path)
#    contents = [item for item in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, item))]
# print(contents)
# if contents:
#    print('here')
# image = [ cl.Image(name=contents[0], display="inline", path=directory_path + contents[0]) ]
# await image.send()
# async with aiofiles.open(directory_path + contents[0], "rb") as f:
#     image_content = await f.read()
#     image2 = cl.Image(name=contents[0], display="inline", content=image_content)
#     await image2.send()
#   path = directory_path + contents[0]
#  elements = [
#     cl.Image(name=contents[0], display="inline", path=path)
# ]
# await cl.Message(content="Here is the graph!", elements=elements).send()
# "res" is a Dict. For this chain, we get the response by reading the "text" key.
# This varies from chain to chain, you should check which key to read.
