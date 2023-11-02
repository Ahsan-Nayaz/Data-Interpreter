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


def delete_directory_contents(directory_path):
    try:
        # Check if the directory exists
        if os.path.exists(directory_path):
            # Iterate over all files and subdirectories in the directory
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)

                # If it's a file, delete it
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                # If it's a directory, delete it recursively
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            print(f"Contents of '{directory_path}' have been deleted.")
        else:
            print(f"The directory '{directory_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def is_directory_empty(directory_path):
    try:
        # Check if the directory exists
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            # Check if the directory is empty
            if not os.listdir(directory_path):
                return True
            else:
                return False
        else:
            print(f"The directory '{directory_path}' does not exist or is not a directory.")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


async def chat_output(msg, chunk):
    language = 'python'
    # if 'message' in chunk.keys():
    await msg.stream_token(token=str([values for values in chunk.values()][-1]))

    # Code
    # if "language" in chunk:
    #     language = chunk['language']
    # if "executing" in chunk:
    #     await cl.Message(content=chunk['executing']['code'], language=chunk['executing']['language']).send()
    #     # await msg.stream_token(token=str(chunk['executing']))
    # Output
    if "output" in chunk:
        await msg.stream_token(token=chunk['output'])


@cl.on_chat_start
async def main():
    unique_id = uuid.uuid4()
    print(unique_id)
    # Instantiate the chain for that user session
    # Store the chain in the user session
    interpreter.model = "azure/gpt-4-32k-0613"
    interpreter.context_window = 32000
    # interpreter.auto_run = True
    interpreter.system_message += """
    Files Available:
                1. /home/azureuser/data/leeds_dna_v5.csv 
                2. /home/azureuser/data/dudley.csv
    Ask the user which file he wants to use, then proceed.
    You are to perform as a Data Engineer for a project where we have to predict DNA(Did not Attend) for patient appointments.
    Use this file and perform the following steps on it. (use python only):
    1. Data Transformation
        * Clean the dataframe. Only remove the columns which have no values or is will not be relevant to the prediction. Impute missing values in place of rows.
        * Also you need to create a "dna" column(which is basically a column referring to whether a patient attended the appointment or not) from the dataframe which might be under a different name, the values should be '0' for whoever attended otherwise whatever values are there, it should be a '1'. If there is already a binary value column for it then just rename it as "dna".
        * If there is a datetime column, confirm with user, (Ask user if date is American or European format) handle it accordingly and also perform datetime split on train and test data. Otherwise ask the user for the kind of split he/she wants, be careful to do the split before transformaing the data.
        * Do not transform the target column to tensors. It should remain in it's data types. Just split it into y_test and y_train.
        * The first pre-processing step should be to check data types and confirm assumptions with the user.
        * Identify/confirm data types
        * Deal with missing values
        * Perform feature engineering
        * Perform encoding/scaling
        * use a column transformer, and then Use helmert encoder for categorical columns, and a min max scaler for numerical columns.
                cat_transformer = Pipeline(steps=[
                    ('enc', HelmertEncoder(handle_unknown='return_nan'))])
                num_transformer = Pipeline(steps=[
                    ('scaler', MinMaxScaler())])
                preprocessor = ColumnTransformer(transformers=[('num', num_transformer, numerical_columns),
                                                               ('cat', cat_transformer, categorical_columns)])
        * In the end the data should be transformed in such a way that it can be fed into a TENSORFLOW neural network.
        * In the end there should X_test, X_train, y_train and y_test.
        You can perform other techniques which you think are necessary.
    Ask the user for feedback after every step then finally save the transformed data with feature engineering(if necessary).
    Ask the user if he/she has any feature engineering suggestions. 
    Before executing any execution 
    Suggest  actions but wait for confirmation or an alternative from the user before actioning them. 
    Before executing any code, ask for user's confirmation.
    """

    # llm_chain = cl.make_async(interpreter.chat)
    llm_chain = interpreter.chat
    # Wait for the user to upload a file
    # file = await cl.AskFileMessage(
    #    content="Please upload a file to begin!", accept={"text/plain": [".csv", ".pdf", ".txt", ".xlsx"]}
    # ).send()
    cl.user_session.set("llm_chain", llm_chain)
    # cl.user_session.set("files", file[0])
    cl.user_session.set("unique_id", unique_id)
    # create_file(file[0])
    # await cl.Message(
    #   content=f"`{file[0].name}` uploaded"
    # ).send()


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


def create_file(file):
    # Check if the file type is one of the accepted types
    unique_id = cl.user_session.get("unique_id")
    print(unique_id)
    accepted_types = [".csv", ".pdf", '.xlsx']  # Add more if needed
    for val in accepted_types:
        # print(file)
        if val not in file.name:
            # Handle invalid file type
            print("Invalid file type. Please upload a valid file.")
        else:
            # File type is valid, proceed to create and fill the new file
            if not os.path.exists(str(unique_id)):
                # Create the directory
                os.makedirs(f"data/file/")
                os.makedirs(f"data/graph/")

            if val == '.xlsx':
                df = pd.read_excel('/Users/ahsan_admin/Downloads/' + file.path)

                # Do some operations on the DataFrame if needed
                # For example, you can manipulate the data in df.

                # Save the DataFrame to a new XLSX file at the specified output location
                df.to_excel(f'data/file/{file.name}', index=False)
            elif val == '.pdf':
                text = file.content.decode("latin-1")

                # Create a new file and write the text to it
                new_file_name = file.name
                with open(f"data/file/{new_file_name}", "w", encoding="latin-1") as new_file:
                    new_file.write(text)
            else:

                text = file.content.decode("utf-8")

                # Create a new file and write the text to it
                new_file_name = file.name
                with open(f"data/file/{new_file_name}", "w", encoding="utf-8") as new_file:
                    new_file.write(text)

            print(f"File created: {file.name}")
