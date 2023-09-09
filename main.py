from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from rajiv import Rajiv

load_dotenv()

app = FastAPI()

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


async def initializeTeams():
    print("teams")


async def delegate(questions):
    print("delegate")


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

        summary = initializeTeams()

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
