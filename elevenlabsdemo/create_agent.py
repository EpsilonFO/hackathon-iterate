# from elevenlabs import ElevenLabs

# client = ElevenLabs(

#     base_url="https://api.elevenlabs.io"

# )

# client.conversational_ai.agents.create(
#     "conversation_config": {
#         "agent": {
#             "prompt": "You are a helpful assistant...",
#             "llm": {
#                 "model": "claude-sonnet-4-5",
#                 "temperature": 0.2
#             },
#             "language": "en",
#             "first_message": "Hey there, I'm the assistant of the pharmacy. Who's there ?"
#         }
#     }
# )

from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="sk_acc9ecd482027239bd81b5f096013a5c7c0476a130e6aecd")

agent = client.conversational_ai.agents.create(
    name="Mon Agent",
    conversation_config={
        "agent": {
            "prompt": {
                "prompt": "You are an AI agent for a pharmacy, that asks to the suppliers calling what is new about their products, their price changings and their delivery time."
            },
            "first_message": "Hey there, I'm the assistant of the pharmacy. Who's there ?",
            "language": "en"
        },
        "tts": {
            "voice_id": "Xb7hH8MSUJpSbSDYk0k2"
        }
    }
)

print(agent)