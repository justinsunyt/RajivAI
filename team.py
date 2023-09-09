import openai
import os
import json
from typing import List
from termcolor import colored
from fastapi import WebSocket
from dotenv import load_dotenv
import asyncio


class Team:
    def __init__(self, context, websocket: WebSocket):
        load_dotenv()
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.context = context
        self.websocket = websocket

    async def summarize(self):
        prompt = f"""
            You are a college teaching assistant. Summarize the following lecture notes:

            \\CONTEXT\\

            Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness.
            Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects.
            Rely strictly on the provided text, without including external information.
            Format the summary in paragraph form for easy understanding.
        """
        prompt = prompt.replace("\\CONTEXT\\", self.context)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[{"role": "system", "content": prompt}],
            stream=True,
        )
        response_str = ""
        for chunk in response:
            if "content" in chunk["choices"][0]["delta"]:
                token = chunk["choices"][0]["delta"]["content"]
                response_str += token
                print(colored(token, "green"), end="", flush=True)
                await self.websocket.send_text(token)
                await asyncio.sleep(0.01)
        return response_str

    async def generate(self, question):
        prompt_1 = f"""
            You are a college teaching assistant designed to help a fellow professor generate an exam and answer key for their course.
        """

        prompt_2 = f"""
            You are a college teaching assistant designed to help a fellow professor generate an exam and answer key for their course.
        """

        prompt_1 = prompt_1.replace("\\QUESTION\\", question)
        prompt_2 = prompt_2.replace("\\QUESTION\\", question)

        messages_1 = [{"role": "system", "content": prompt_1}]
        messages_2 = [{"role": "system", "content": prompt_2}]

        response_1 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=messages_1,
            stream=True,
        )

        response_2 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=messages_2,
            stream=True,
        )
