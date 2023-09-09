import openai
import os
import json
from typing import List
from termcolor import colored
from fastapi import WebSocket
from dotenv import load_dotenv
import asyncio


class Rajiv:
    def __init__(self, delegate, websocket: WebSocket):
        load_dotenv()
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.delegate = delegate
        self.websocket = websocket

    async def run(self, messages: List[dict]):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0,
            messages=messages,
            stream=True,
            functions=[
                {
                    "name": "delegate",
                    "description": "Delegate questions for each TA team",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "questions": {
                                "type": "array",
                                "description": "The TA team to generate the question, followed by the topic, difficulty, and format of each question",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "The name of the TA team",
                                        },
                                        "topic": {
                                            "type": "string",
                                            "description": "The topic of the question",
                                        },
                                        "difficulty": {
                                            "type": "string",
                                            "description": "The difficulty of the question",
                                        },
                                        "format": {
                                            "type": "string",
                                            "description": "The format of the question",
                                        },
                                    },
                                },
                            },
                        },
                        "required": ["questions"],
                    },
                },
            ],
            function_call="auto",
        )
        response_str = ""
        raw_function_name = ""
        raw_function_args = ""
        for chunk in response:
            if "content" in chunk["choices"][0]["delta"]:
                token = chunk["choices"][0]["delta"]["content"]
                if token != None:
                    response_str += token
                    print(colored(token, "green"), end="", flush=True)
                    await self.websocket.send_text(token)
                    await asyncio.sleep(0.01)
            if chunk["choices"][0]["delta"].get("function_call"):
                raw_function = chunk["choices"][0]["delta"]["function_call"]
                if "name" in raw_function:
                    raw_function_name = raw_function["name"]
                raw_function_args += raw_function["arguments"]
        messages.append({"role": "assistant", "content": response})

        if raw_function_name != "":
            print("\n\n")
            print(raw_function_args)

            await asyncio.sleep(0.01)

            function_args = json.loads(raw_function_args)
            function_response = await self.delegate(
                questions=function_args.get("questions"),
            )
            messages.append(
                {
                    "role": "function",
                    "name": raw_function_name,
                    "content": str(function_response),
                }
            )
