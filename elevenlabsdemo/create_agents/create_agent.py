from elevenlabs import ElevenLabs
from dotenv import load_dotenv
from elevenlabsdemo.create_agents.systprompt import SYSTEM_PROMPT_BUY_SEARCH_NEW_PRICES

import os

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

agent = client.conversational_ai.agents.update(
    agent_id=os.getenv("AGENT_ID"),
    name="Mon Agent",
    conversation_config={
        "agent": {
            "prompt": {
                "prompt": SYSTEM_PROMPT_BUY_SEARCH_NEW_PRICES,
                "llm": "claude-sonnet-4-5"
            },
            "first_message": "Hey there, I'm Alexis, the assistant of the pharmacy. Who's there ?",
            "language": "en"
        },
        "tts": {
            "voice_id": "Xb7hH8MSUJpSbSDYk0k2"
        }
    }
)

print(agent)