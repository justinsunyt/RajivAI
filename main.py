from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from rajiv import Rajiv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from typing import List
from team import Team

load_dotenv()

app = FastAPI()

chunks = []

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initializeTeams(chunks: List[str], websocket: WebSocket):
    teams : List[Team] = []
    summary = ""
    index = 0
    for chunk in chunks:
        teams.append(Team(index, chunk, websocket))
        index+=1
    for team in teams:
        summary += team.summarize()
    return summary

async def delegate(questions):
    print("delegate")

def tiktoken_len(text):
    tokens = tiktoken.get_encoding("cl100k_base").encode(text, disallowed_special=())
    return len(tokens)

@app.get("/")
async def root(pdf: str):
    global chunks

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=14500,
        chunk_overlap=1000,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(pdf)

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        instructions = await websocket.receive_json()
        messages = []

        prompt_1 = f"""
            You are RajivAI, a college professor designed to help a fellow professor generate an exam and answer key for their course.
            The professor has given you the following instructions regarding the exam:

            \\INSTRUCTIONS\\

            You are responsible for coming up with the exam format.
            If not already specified in instructions, this includes the number of questions and the point distribution of each question.
            You have access to a team of teaching assistants in teams that will generate each question.
            Each team of TAs only knows an exclusive part of the course material.
            They will now tell you what they each know about the course so you can understand the general material and delegate tasks appropriately.

            \\SUMMARY\\

            Now, generate the test format and give each question to TAs using the "delegate" function.
            For each question, you should specify which TA to designate it to, and its general topic, difficulty, and format.
        """

        summary = initializeTeams(chunks, websocket)

        prompt_1 = prompt_1.replace("\\INSTRUCTIONS", instructions)
        prompt_1 = prompt_1.replace("\\SUMMARY\\", summary)

        messages = [{"role": "system", "content": prompt_1}]

        rajiv = Rajiv(delegate, websocket)
        while True:
            user_input = await websocket.receive_json()
            messages.extend(user_input)
            await rajiv.run(messages)
    except RuntimeError as e:
        print(e)
    except WebSocketDisconnect:
        await websocket.send_text({"role": "system", "content": "Error"})
