import os
import re
import time
from random import randint

import pytest

from interpreter.core.core import Interpreter
from interpreter.utils.count_tokens import count_messages_tokens, count_tokens

interpreter = Interpreter()
interpreter.auto_run = True
interpreter.model = "azure/gpt-4-32k-0613"
interpreter.temperature = 0
interpreter.context_window = 32000


# this function will run before each test
# we're clearing out the messages Array so we can start fresh and reduce token usage
def setup_function():
    interpreter.messages = []
    interpreter.temperature = 0
    interpreter.auto_run = True
    interpreter.model = "azure/gpt-4-32k-0613"
    interpreter.debug_mode = False


# this function will run after each test
# we're introducing some sleep to help avoid timeout issues with the OpenAI API
def teardown_function():
    time.sleep(5)


def test_config_loading():
    # because our test is running from the root directory, we need to do some
    # path manipulation to get the actual path to the config file or our config
    # loader will try to load from the wrong directory and fail
    currentPath = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(currentPath, "./config.test.yaml")

    interpreter.extend_config(config_path=config_path)

    # check the settings we configured in our config.test.yaml file
    temperature_ok = interpreter.temperature == 0.25
    model_ok = interpreter.model == "azure/gpt-4-32k-0613"
    debug_mode_ok = interpreter.debug_mode == True

    assert temperature_ok and model_ok and debug_mode_ok


def test_system_message_appending():
    ping_system_message = (
        "Respond to a `ping` with a `pong`. No code. No explanations. Just `pong`."
    )

    ping_request = "ping"
    pong_response = "pong"

    interpreter.system_message += ping_system_message

    messages = interpreter.chat(ping_request)

    assert messages == [
        {"role": "user", "message": ping_request},
        {"role": "assistant", "message": pong_response},
    ]


def test_reset():
    # make sure that interpreter.reset() clears out the messages Array
    assert interpreter.messages == []


def test_hello_world():
    hello_world_response = "Hello, World!"

    hello_world_message = f"Please reply with just the words {hello_world_response} and nothing else. Do not run code. No confirmation just the text."

    messages = interpreter.chat(hello_world_message)

    assert messages == [
        {"role": "user", "message": hello_world_message},
        {"role": "assistant", "message": hello_world_response},
    ]


def test_nested_loops_and_multiple_newlines():
    interpreter.chat(
        """Can you write a nested for loop in python and shell and run them(should also terminate at some point)? Don't forget to properly format your shell script and use semicolons where necessary. Also put 1-3 newlines between each line in the code. Only generate and execute the code. No explanations. Thanks!"""
    )


def test_write_to_file():
    interpreter.chat("""Write the word 'Washington' to a .txt file called file.txt""")
    assert os.path.exists("file.txt")
    interpreter.messages = []  # Just reset message history, nothing else for this test
    messages = interpreter.chat(
        """Read file.txt in the current directory and tell me what's in it."""
    )
    assert "Washington" in messages[-1]["message"]


def test_markdown():
    interpreter.chat(
        """Hi, can you test out a bunch of markdown features? Try writing a fenced code block, a table, headers, everything. DO NOT write the markdown inside a markdown code block, just write it raw."""
    )
