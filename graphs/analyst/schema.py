# graphs/analyst/schema.py
from pydantic import BaseModel, Field
from typing import Optional, Any, Literal

class AnalysisSchema(BaseModel):
    reasoning: str = Field(description="Detailed reasoning process of the analysis")
    summary: str = Field(description="Concise summary of the analysis")
    todo_next: Optional[str] = Field(default=None, description="Next steps or actions to be taken based on the analysis.\n" +\
        "Examples: 'Use the Stock Price Tool to get the latest stock prices.'\n" +\
        "If no further action is needed, return an empty string.")


# recommendation 고도화 예정
class ReportSchema(BaseModel):
    plan: str = Field(description="Before generating the report, outline your plan for structuring it")
    title: str = Field(description="Title of the report")
    key_considerations: str = Field(description="Key considerations to keep in mind while analyzing the data")
    indicators_table: str = Field(description="A table of important indicators relevant to the analysis")
    detailed_analysis: str = Field(description="In-depth analysis of the data")
    conclusion: str = Field(description="Final conclusion drawn from the analysis")
    recommendation: Literal["Buy", "No Action", "Sell"] = Field(description="Your recommendation based on the analysis")


def get_tool_schema(available_tools: dict) -> BaseModel:

    class ToolParameterSchema(BaseModel):
        parameter_name: str = Field(description="Name of the parameter")
        value: Any = Field(description="Value of the parameter")

    class ToolSchema(BaseModel):
        tool_name: str
        params: list[ToolParameterSchema]

    class ToolListSchema(BaseModel):
        reasoning: str = Field(description="Reasoning for choosing the tools and their parameters")
        tools: list[ToolSchema] = Field(
            description="List of tools to be used with their parameters.\n" +\
            "Each tool must be one of:\n" + ", ".join(map(lambda x: f"{x}", available_tools.keys())) + "\n" +\
            f"Available parameters for each tool: {', '.join([f'{v.get('name')}: {v.get('params')}' for v in available_tools.values()])}"
        )
    
    return ToolListSchema
