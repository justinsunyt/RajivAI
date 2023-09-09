import openai
import os
from termcolor import colored
from fastapi import WebSocket
from dotenv import load_dotenv
import asyncio
import json
from ta_tools import query


class Team:
    def __init__(self, name, context, websocket: WebSocket):
        load_dotenv()
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.name = name
        self.context = context
        self.websocket = websocket
        self.available_functions = {
            "solve": query
        }

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
            You are a college teaching assistant helping your professor create a question and answer for their exam.
            The professor has given you the following details regarding the question:

            Topic: \\QUESTION\\
            Difficulty: \\DIFFICULTY\\
            Format: \\SCHEME\\
                
            You know the following course material:

            \\CONTEXT\\
            
            You are partnered with another TA, who was given the same details and context.
            You are responsible for generating the question and the answer key with explanations.
            Rely strictly on the provided material and the professor's instructions, without including external information.
            Your partner will give feedback on the question. Refine your question accordingly.
            Only output the question and the answer. 
            Do not converse with the other TA on anything.

            Good luck! Begin.
        """

        prompt_2 = f"""
            You are a very critical and analytical college teaching assistant helping your professor create a question and answer for their exam.
            The professor has given you the following details regarding the question:

            Topic: \\QUESTION\\
            Difficulty: \\DIFFICULTY\\
            Format: \\SCHEME\\

            The professor has also given you the following context:

            \\CONTEXT\\

            You are partnered with another TA, who was given the same details and context.
            You are will receive your partner's question and answers. Without looking at the answer key, do the question.
            If you have the same answer as the key, use the provided "stop" function and output the final question and answer.
            Rely strictly on the provided text and the professor's instructions, without including external information.
            Give feedback on the question. Your partner will refine their question accordingly.
            Only output constructive feedback. 
            Do not converse with the other TA on anything.

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

        iterations = 0
        while (True and iterations < 5):
            print(iterations)
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

            print("\n")
            req_to_2 = f"""
                Here is a question: {response_1_str}
                Do the question without looking at the answer key.
                Then, compare answers. If correct, then use the stop function.
                Otherwise, output suggestions to change the question.
            """
            messages_1.append({"role": "assistant", "content": response_1_str})
            messages_2.append({"role": "user", "content": req_to_2})

            response_2 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                temperature=0,
                messages=messages_2,
                stream=True,
                functions=[
                    {
                        "name": "stop",
                        "description": "When a question is deemed acceptable",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "dummy_property": {
                                    "type": "null",
                                }
                            }
                        },
                        "required": []
                    }
                ]
            )

            response_2_str = ""

            raw_function_name = ""        
            raw_function_args = ""
            for chunk in response_2:
                if "content" in chunk["choices"][0]["delta"]:
                    token = chunk["choices"][0]["delta"]["content"]
                    if token != None:
                        response_2_str += token
                        print(colored(token, "blue"), end="", flush=True)
                        await self.websocket.send_text(token)
                        await asyncio.sleep(0.01)
                if chunk["choices"][0]["delta"].get("function_call"):
                    raw_function = chunk["choices"][0]["delta"]["function_call"]
                    if "name" in raw_function:
                        raw_function_name = raw_function["name"]
                    raw_function_args += raw_function["arguments"]

            messages_2.append({"role": "assistant", "content": response_2_str})
            messages_1.append({"role": "user", "content": response_2_str})

            if raw_function_name == "stop":
                iterations = 5
                return response_1_str     

            iterations += 1
