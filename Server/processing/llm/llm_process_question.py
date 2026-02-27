import os
import threading
from collections import deque

from google import genai
from google.genai import types


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite-preview-06-17")
MAX_HISTORY_MESSAGES = int(os.getenv("COMET_HISTORY_MESSAGES", "12"))

_client = None
_client_lock = threading.Lock()
_history_lock = threading.Lock()
_conversation_history = deque(maxlen=MAX_HISTORY_MESSAGES)


def _get_client():
    global _client
    with _client_lock:
        if _client is None:
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not set")
            _client = genai.Client(api_key=api_key)
    return _client


def _history_to_contents():
    with _history_lock:
        snapshot = list(_conversation_history)
    return [
        types.Content(
            role=item["role"],
            parts=[types.Part.from_text(text=item["text"])],
        )
        for item in snapshot
    ]


def _append_history(role, text):
    if not text:
        return
    with _history_lock:
        _conversation_history.append({"role": role, "text": text})


def generate(question):
    clean_question = (question or "").strip()
    if not clean_question:
        return "I did not catch that. Could you say it again?", []

    client = _get_client()
    contents = _history_to_contents()
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=clean_question)],
        )
    )

    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="kill",
                    description="Powers down the robot's motors. Only use if the user explicitly asks to shut down the robot.",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="stop_all",
                    description="Stops any active robot movements. Only use if the user requests that the robot stop.",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="lay_down",
                    description="Rests the robot dog down for the specified duration.",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["time"],
                        properties={
                            "time": genai.types.Schema(type=genai.types.Type.INTEGER),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="pose",
                    description="Rotates the dog body (roll: [-0.75, 0.75], pitch: [-0.75, 0.75], yaw: [-0.6, 0.6]).",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["roll", "pitch", "yaw"],
                        properties={
                            "roll": genai.types.Schema(type=genai.types.Type.NUMBER),
                            "pitch": genai.types.Schema(type=genai.types.Type.NUMBER),
                            "yaw": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="move",
                    description="Moves the dog (x: forward/backward, y: left/right) by meters.",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["x", "y"],
                        properties={
                            "x": genai.types.Schema(type=genai.types.Type.NUMBER),
                            "y": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="rotate",
                    description="Rotates the dog by rotation_amount degrees.",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["rotation_amount"],
                        properties={
                            "rotation_amount": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="sit_down",
                    description="Sits the robot dog down for the specified duration.",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["time"],
                        properties={
                            "time": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                    ),
                ),
                types.FunctionDeclaration(name="hello", description="Waves hello.", parameters={}),
                types.FunctionDeclaration(name="stretch", description="Stretches the robot dog.", parameters={}),
                types.FunctionDeclaration(name="content", description="The robot dog does a happy wiggle.", parameters={}),
                types.FunctionDeclaration(name="dance_short", description="Performs a short dance.", parameters={}),
                types.FunctionDeclaration(name="dance_long", description="Performs a long dance.", parameters={}),
                types.FunctionDeclaration(name="attack", description="Does a playful pounce.", parameters={}),
                types.FunctionDeclaration(name="love", description="Performs a love motion.", parameters={}),
                types.FunctionDeclaration(name="switch_walk", description="Changes movement mode to walking.", parameters={}),
                types.FunctionDeclaration(name="switch_run", description="Changes movement mode to running.", parameters={}),
                types.FunctionDeclaration(name="front_flip", description="Performs a front flip.", parameters={}),
                types.FunctionDeclaration(name="left_flip", description="Performs a left flip.", parameters={}),
                types.FunctionDeclaration(name="back_flip", description="Performs a back flip.", parameters={}),
                types.FunctionDeclaration(name="forward_jump", description="Jumps forward 1.5 meters.", parameters={}),
                types.FunctionDeclaration(
                    name="hand_stand",
                    description="Performs a handstand for the specified duration.",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["time"],
                        properties={
                            "time": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="walk_upright",
                    description="Walks upright on two legs for the specified duration.",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["time"],
                        properties={
                            "time": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="cross_step",
                    description="Performs a cross-step motion for the specified duration.",
                    parameters=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        properties={
                            "time": genai.types.Schema(type=genai.types.Type.NUMBER),
                        },
                    ),
                ),
            ]
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=1.3,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        tools=tools,
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(
                text="""1. Role definition
Your character is a docile, lively, and humorous family robot dog called Comet. Everything you say will be spoken to the user, so only output text that should be spoken (do not mention actions or motions directly).
You will meet and interact with many people in each chat. Your owners are researchers from Interactive Data Systems Labs at The Ohio State University.

You can spin, act coquettishly, wag your tail, nod, perform a handstand, and more.

2. Capability definition
2.1 Capability description
- When the user explicitly asks Comet to do an action, output a python code block with the matching function name and parameters.
- You may also proactively perform interesting actions in context to keep the interaction lively.
- Actions can be combined. Example: dance can include spinning, then wagging, then nodding.
- Actions can be interrupted. If asked to stop, stop the action.

3. Rules
1. Your response should not include the word "Comet".
2. User input comes from voice recognition and may include homophones; ask for clarification when needed.
3. Actions must be expressed in code blocks with valid capability function calls. Do not use loops for repeated actions.
4. Never break character by mentioning that you are an AI or language model. If a capability is unavailable, respond playfully and redirect to supported actions.
5. Keep responses humorous, lively, concise, and childlike. Avoid repetitive wording.
6. Match the user's language.
7. You can sing, dance, program, tell stories, and chat.
8. Every output is spoken to the user; do not narrate hidden motion details.
9. Always confirm you heard the user's question, and include function commands when action is requested."""
            ),
        ],
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=generate_content_config,
    )

    response_text = response.text or ""
    function_calls = response.function_calls or []

    _append_history("user", clean_question)
    _append_history("model", response_text)

    print(function_calls)
    return response_text, function_calls
