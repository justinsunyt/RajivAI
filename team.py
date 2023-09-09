import openai
import os
from termcolor import colored
from fastapi import WebSocket
from dotenv import load_dotenv
import asyncio
import json


class Team:
    def __init__(self, name, context, websocket: WebSocket):
        load_dotenv()
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.name = name
        self.context = context
        self.websocket = websocket

    async def summarize(self):
        prompt = f"""
            You are a college teaching assistant. Summarize the following lecture notes:

            \\CONTEXT\\
            
            List the topics and techniques covered concisely.
            Rely strictly on the provided text, without including external information.
            Format the summary in bullet point form.
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

    async def generate(self, question, difficulty, scheme):
        prompt_1 = f"""
            You are a college teaching assistant designed to help a fellow professor generate an exam and answer key for their course.
            The professor has given you the following details regarding the question:

            Topic: \\QUESTION\\
            Difficulty: \\DIFFICULTY\\
            Format: \\SCHEME\\

            The professor has also given you the following context:

            \\CONTEXT\\
            
            You are partnered with another TA, who was given the same question and context.
            You are responsible for generating the question and the answer key.
            Rely strictly on the provided text and the professor's instructions, without including external information.
            Your partner will give feedback on the question. Refine your question accordingly.

            Good luck! Begin.
        """

        prompt_2 = f"""
            You are a college teaching assistant designed to help a fellow professor generate an exam and answer key for their course.
            The professor has given you the following details regarding the question:

            Topic: \\QUESTION\\
            Difficulty: \\DIFFICULTY\\
            Format: \\SCHEME\\

            The professor has also given you the following context:

            \\CONTEXT\\

            You are partnered with another TA, who was given the same question and context.
            You are responsible for validating your partner's question and answer key.
            Rely strictly on the provided text and the professor's instructions, without including external information.
            Give feedback on the question. Your partner will refine their question accordingly.

            Good luck! Begin.
        """

        prompt_1 = prompt_1.replace("\\QUESTION\\", question)
        prompt_1 = prompt_1.replace("\\DIFFICULTY\\", difficulty)
        prompt_1 = prompt_1.replace("\\SCHEME\\", scheme)
        prompt_1 = prompt_1.replace("\\CONTEXT", self.context)
        prompt_2 = prompt_2.replace("\\QUESTION\\", question)
        prompt_2 = prompt_2.replace("\\DIFFICULTY\\", difficulty)
        prompt_2 = prompt_2.replace("\\SCHEME\\", scheme)
        prompt_2 = prompt_2.replace("\\CONTEXT", self.context)

        messages_1 = [{"role": "system", "content": prompt_1}]
        messages_2 = [{"role": "system", "content": prompt_2}]

        for x in range(0, 2):
            response_1 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                temperature=0,
                messages=messages_1,
                stream=True,
            )

            response_1_str = ""

            for chunk in response_1:
                if "content" in chunk["choices"][0]["delta"]:
                    token = chunk["choices"][0]["delta"]["content"]
                    response_1_str += token
                    print(colored(token, "green"), end="", flush=True)
                    await self.websocket.send_text(token)
                    await asyncio.sleep(0.01)

            messages_1.append({"role": "assistant", "content": response_1_str})
            messages_2.append({"role": "user", "content": response_1_str})

            response_2 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                temperature=0,
                messages=messages_2,
                stream=True,
                # function = [
                #     {
                #         "name": "solve",
                #         "description": "A tool only for when you are stuck. It simplifies/solves a final equations or find simple facts required to solve the given question",
                #         "parameters": {
                #             "type": "object",
                #             "properties": {
                #                 "query": {
                #                     "type": "string",
                #                     "description": "the final equation or question to solve"
                #                 }
                #             },
                #         },
                #         "required": ["query"]
                #     }
                # ]
            )

            response_2_str = ""

            for chunk in response_2:
                if "content" in chunk["choices"][0]["delta"]:
                    token = chunk["choices"][0]["delta"]["content"]
                    response_2_str += token
                    print(colored(token, "green"), end="", flush=True)
                    await self.websocket.send_text(token)
                    await asyncio.sleep(0.01)

            # raw_function_name = ""
            # raw_function_args = ""
            # for chunk in response_2:
            #     if "content" in chunk["choices"][0]["delta"]:
            #         token = chunk["choices"][0]["delta"]["content"]
            #         if token != None:
            #             response_str += token
            #             print(colored(token, "green"), end="", flush=True)
            #             await self.websocket.send_text(token)
            #             await asyncio.sleep(0.01)
            #     if chunk["choices"][0]["delta"].get("function_call"):
            #         raw_function = chunk["choices"][0]["delta"]["function_call"]
            #         if "name" in raw_function:
            #             raw_function_name = raw_function["name"]
            #         raw_function_args += raw_function["arguments"]
            # messages_2.append({"role": "assistant", "content": response_2})

            # if raw_function_name != "":
            #     print("\n\n")
            #     print(raw_function_args)

            #     await asyncio.sleep(0.01)

            #     function_args = json.loads(raw_function_args)
            #     function_response = await self.delegate(
            #         questions=function_args.get("questions"),
            #     )
            #     messages.append(
            #         {
            #             "role": "function",
            #             "name": raw_function_name,
            #             "content": str(function_response),
            #         }
            #     )

            # messages_2.append({"role": "assistant", "content": response_2_str})
            # messages_1.append({"role": "user", "content": response_2_str})
