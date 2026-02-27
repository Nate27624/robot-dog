# Comet
Creating an LLM driven robot dog with Unitree Go 2, Google Gemini, and other types of AI

## Unity
This is the Android application which enables communication with the controller via Flask.  The android application uses Wit.AI for speech input processing and speaking output (STT and TTS)

## Controller
Allows commands to be sent to the robot dog as well as text to be spoken to the android application.  Relays information to be processed to the server, and takes responses from the server to be processed and returned back to this controller

## Server
Does the data processing. Receives data from the controller, processes it, and communicates back to the controller with a corresponding output to perform with that data.
