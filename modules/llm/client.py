# modules/llm/client.py
import google.genai as genai
from google.genai import types
from pydantic import BaseModel
import json

class Response:
    def __init__(
            self,
            model: str,
            content: dict,
            input_tokens: int,
            output_tokens: int,
    ):
        self.model = model
        self.content = content
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

class Client:
    def __init__(self):
        self.client = genai.Client()

    def _check_schema(self, schema: BaseModel, content: str) -> bool:
        try:
            schema.model_validate_json(content)
            return True
        except Exception:
            return False
    
    def generate_content(
                self,
                model: str,
                contents: list,
                system_instruction: str = None,
                thinking_budget: int = -1,
                schema: BaseModel = None,
        ) -> Response:

        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
            system_instruction=system_instruction,
            response_mime_type=None if schema is None else "application/json",
            response_schema=schema
        )

        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        text = response.text
        content = {'text': text}
        data = Response(
            model=model,
            content=content,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.total_token_count
        )

        if not schema:
            return data
        
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        
        while not self._check_schema(schema, text):
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            text = response.text
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            
            data.input_tokens += response.usage_metadata.prompt_token_count
            data.output_tokens += response.usage_metadata.total_token_count
        
        content = json.loads(text)
        data.content = content
        return data



# Test: python -m modules.llm.client
if __name__ == "__main__":

    class Recipe(BaseModel):
        recipe_name: str
        ingredients: list[str]
    
    llm_client = Client()
    response = llm_client.generate_content(
        model="gemini-2.5-flash",
        contents=["List a few popular cookie recipes, and include the amounts of ingredients."],
        thinking_budget=0,
        schema=Recipe,
    )
    
    print(response.content.get('ingredients'))