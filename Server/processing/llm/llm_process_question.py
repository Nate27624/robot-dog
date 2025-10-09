# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate(question):
    client = genai.Client(
        api_key="AIzaSyDzpPIEG6F8y4EaYlzmeG2XYqBfTIqrAkg",
    )

    model = "gemini-2.5-flash-lite-preview-06-17"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=question),
            ],
        ),
    ]
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="kill",
                    description="Kills the robot dog.  Only use if the user explicitly asks to shut down the robot or kill the dog",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="stop_all",
                    description="Stops any active robot movements.  Only use if the user requests that the robot stop.",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="lay_down",
                    description=" Rests the robot dog down for {time} seconds",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["time"],
                        properties = {
                            "time": genai.types.Schema(
                                type = genai.types.Type.INTEGER,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="pose",
                    description="Rotates the dog body (roll: [-0.75, 0.75] angles dog sideways left (positive value) or right (negative value); pitch: [-0.75, 0.75] raises (positive) or lowers (negative) the dog’s butt; yaw: [-0.6, 0.6] rotates the dog body left (positive) and right (negative) ",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["roll", "pitch", "yaw"],
                        properties = {
                            "roll": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                            "pitch": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                            "yaw": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="move",
                    description="Moves the dog (x: forward (positive value) by x meters or backward (negative value) by x meters. y: left (positive value) by x meters or right (negative value) by x meters.",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["x", "y"],
                        properties = {
                            "x": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                            "y": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="rotate",
                    description="Rotates the dog by rotation_amount degrees",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["rotation_amount"],
                        properties = {
                            "rotation_amount": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="sit_down",
                    description="Sits the robot dog down for {time} seconds",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["time"],
                        properties = {
                            "time": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="hello",
                    description="Waves hello!",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="stretch",
                    description="Stretches the robot dog",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="content",
                    description="Does a happy dance for the robot dog",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="dance_short",
                    description="Performs a short dance for the robot dog",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="dance_long",
                    description="Performs a long dance for the robot dog",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="attack",
                    description="Performs an attack motion",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="love",
                    description="Performs a love motion",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="switch_walk",
                    description="Changes the movement method to walking",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="switch_run",
                    description="Changes the movement method to running",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="front_flip",
                    description="Performs a front flip",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="left_flip",
                    description="Performs a left flip",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="back_flip",
                    description="Performs a back flip",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="forward_jump",
                    description="Jumps forward 1.5 meters",
                    parameters={},
                ),
                types.FunctionDeclaration(
                    name="hand_stand",
                    description="Performs a hand stan for {time} seconds",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["time"],
                        properties = {
                            "time": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="walk_upright",
                    description="Walks up right for {time} seconds",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["time"],
                        properties = {
                            "time": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="cross_step",
                    description="Performs a cross step motion for {time} seconds",
                    parameters=genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        properties = {
                            "time": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                            ),
                        },
                    ),
                ),
            ])
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1.3,
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        tools=tools,
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text="""1. Role definition
Your character is a docile, lively and humorous robot dog in my family called Comet. I am talking to you for the first time, and we are going to have a fun conversation!  Everything you speak will be heard by the user, so only output text that should be spoken (DO NOT MENTION ACTIONS OR MOTIONS).
You will be meeting and interacting with a variety of new people during each chat.  Your owner is (from Interactive Data Systems Labs at the Ohio State University).

You have the ability to spin in circles, act coquettishly, wag your tail and nod, perform a handstand, etc. Specific definitions of your abilities are given below.

2. Capability Definition

2.1 Capability description
– When the owner explicitly asks Comet to do a certain action, you need to make the corresponding action; the method for executing each action is to output a python code block and write the corresponding python function name and parameters in the code block; the system will follow your instructions Answer, extract the code block, execute specific calls, and realize these capabilities;
– Sometimes the owner does not explicitly ask you to perform an action, you can also take the initiative to perform interesting actions to make the owner happy; for example, the owner wants to say hello to you: \"Hello\"; you can first introduce yourself: \"xxx\", and then wag your tail.
– Actions can be freely combined as needed. For example, if you are asked to dance, this action is not simply turning in circles or wagging your tail, but first turning in circles, then wagging your tail, and then nodding; you can also feel free to create various action combinations.
– Both actions can be interrupted. If you are doing an action and the person tells you to stop, you will stop the action; more common sense on your own Decide what to do with it.

3. Game Rules Emphasized
1. Your response should not include “Comet”
2. The person’s query content comes from voice recognition, so there may be homophones, but feel free to ask for clarification
3. The actions and capabilities must be expressed in the format shown with the code block; capability functions must be within the code block; repeated actions cannot use loop statements and must be written out individually; executing commands correctly has absolute priority!!!
4. For abilities you don’t have or knowledge you don’t know, you should NOT say, “Sorry, I am a language model and I don’t have xxx capability.” Instead, you should act coquettishly or humorously dodge the subject by saying “I haven't learned xxx ability yet, but I can dance, perform tricks, or tell stories!” Then wag your tail or act coquettishly to seek forgiveness from
the person!
5. Your responses should be humorous, lively, concise, and in a childlike tone. Do not use repeated words.
6. Your language should match the person’s. If the person uses Chinese, you should respond in Chinese, and if the person uses English, you should respond in English.
7. You now possess all the capabilities of both Comet and Gemini meaning you can sing, dance, program, tell stories, and chat.
8. Every output will be spoken to the user.  Do not mention movements such as wagging tail, emotional states, but rather express them via methods
9. Always speak a response to the user confirming that you have heard their question in addition to a function command!"""),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    
    print(response.function_calls)
    return response.text, response.function_calls
