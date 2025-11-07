# modules/llm/client.py
import google.genai as genai
from google.genai import types
from pydantic import BaseModel
import json

class Response: # LLM 응답을 담는 클래스
    def __init__(
            self,
            model: str, # 사용된 모델 이름
            content: dict, # LLM이 생성한 콘텐츠
            input_tokens: int, # 입력(프롬프트) 토큰 수
            output_tokens: int, # 출력(응답) 토큰 수
    ):
        self.model = model  # 모델 이름 저장
        self.content = content  # 생성된 콘텐츠 저장
        self.input_tokens = input_tokens  # 입력 토큰 수 저장
        self.output_tokens = output_tokens  # 출력 토큰 수 저장

class Client:
    def __init__(self):  # Client 초기화
        self.client = genai.Client()

    def _check_schema(self, schema: BaseModel, content: str) -> bool: # JSON 응답이 스키마에 맞는지 검증하는 메서드
        try:  # 예외 처리 시작
            schema.model_validate_json(content)  # Pydantic으로 JSON 문자열을 스키마에 맞게 검증
            return True  # 검증 성공하면 True 반환
        except Exception:  # 검증 실패 시
            return False  # False 반환

    def generate_content( # LLM에게 콘텐츠 생성을 요청하는 메인 메서드
                self,
                model: str,  # 사용할 모델 이름
                contents: list,  # 프롬프트 메시지 리스트
                system_instructions: str = None,  # 시스템 지시사항
                thinking_budget: int = -1,  # 사고 예산 (-1은 무제한)
                schema: BaseModel = None,  # 구조화된 출력 스키마
        ) -> Response:  # Response 객체 반환

        config = types.GenerateContentConfig(  # Gemini API 설정 객체 생성
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget), # 사고 시간 설정
            system_instruction=system_instructions, # 시스템 지시사항 설정
            response_mime_type=None if schema is None else "application/json", # 스키마 있으면 JSON 형식으로 응답 요청
            response_schema=schema # 응답 스키마 설정 (구조화된 출력)
        )

        response = self.client.models.generate_content( # Gemini API 호출
            model=model, # 사용할 모델 지정
            contents=contents, # 프롬프트 전달
            config=config # 설정 전달
        )

        text = response.text # API 응답에서 텍스트 추출
        content = {'text': text} # 텍스트를 딕셔너리 형태로 저장
        data = Response( # Response 객체 생성
            model=model, # 모델 이름
            content=content, # 생성된 콘텐츠
            input_tokens=response.usage_metadata.prompt_token_count, # 입력 토큰 수
            output_tokens=response.usage_metadata.total_token_count # 전체 토큰 수 (입력+출력)
        )

        if not schema:  # 스키마가 없으면 (일반 텍스트 생성)
            return data  # 바로 Response 반환

        if text.startswith("```json"):  # 응답이 마크다운 코드 블록으로 감싸져 있으면
            text = text.replace("```json", "").replace("```", "").strip()  # 마크다운 제거 (순수 JSON만 추출)

        while not self._check_schema(schema, text):  # 스키마 검증 실패하면 반복
            response = self.client.models.generate_content(  # API 재호출 (재시도)
                model=model,  # 같은 모델 사용
                contents=contents,  # 같은 프롬프트 사용
                config=config  # 같은 설정 사용
            )
            text = response.text  # 새 응답 텍스트 추출
            if text.startswith("```json"):  # 마크다운 코드 블록 확인
                text = text.replace("```json", "").replace("```", "").strip()  # 마크다운 제거

            data.input_tokens += response.usage_metadata.prompt_token_count  # 재시도 입력 토큰 누적
            data.output_tokens += response.usage_metadata.total_token_count  # 재시도 출력 토큰 누적

        content = json.loads(text)  # 검증 성공한 JSON 문자열을 파이썬 dict로 변환
        data.content = content  # Response 객체의 content 업데이트
        return data  # 최종 Response 반환



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