# modules/llm/client.py
import google.genai as genai
from google.genai import types

class Client:
    def __init__(self):
        self.client = genai.Client()

    def generate_content(
                self,
                model: str,
                contents: list,
                thinking_budget: int = -1
        )-> dict:
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
            )
        )
        content = response.text
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.total_token_count
        return content, input_tokens, output_tokens
    
# Test: python -m modules.llm.client
if __name__ == "__main__":
    llm_client = Client()
    response = llm_client.generate_content(
        model="gemini-2.5-flash",
        contents=["Tell me a joke about programming."]
    )
    print(response)