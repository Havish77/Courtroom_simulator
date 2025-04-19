
import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("GROQ_API_TOKEN")
openai.api_base = "https://api.groq.com/openai/v1"


class BaseAgent:
    def __init__(self, name: str, system_prompt: str, model: str = "llama-3.3-70b-versatile"):
        self.name = name
        self.system_prompt = system_prompt.strip()
        self.history = []
        self.model = model

    def _format_messages(self, user_msg: str):
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_msg})
        return messages

    def respond(self, user_msg: str, **kwargs) -> str:
        messages = self._format_messages(user_msg)
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
                **kwargs
            )
            reply = response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            reply = f"[Error: {str(e)}]"
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": reply})
        return reply
