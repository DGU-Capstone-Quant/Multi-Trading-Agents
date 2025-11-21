# graphs/analyst/agent.py
from modules.agent import Agent
from modules.context import Context
from pydantic import BaseModel
from modules.utils import FINANCIAL_TOOLS, NEWS_TOOLS
from modules.utils import AVAILABLE_TOPICS
from .schema import AnalysisSchema, ReportSchema, get_tool_schema

class AnalystAgent(Agent):
    def __init__(self, task: str):
        super().__init__()
        self.task = task # financial, news, fundamental
        self.history: list[str] = []
        self.tools: dict = {}
        self.todo_next: str = ""
        self._set_tools()
    
    def _add_history(self, content: str, context: Context):
        self.history.append(content)
        context.add_log(
            summary=f"{context.get_cache('ticker','')} - {self.task} 분석 로그 {len(self.history)}",
            content=content,
        )
    
    def _set_tools(self):
        if self.task == "financial":
            self.tools = {tool['name']: tool for tool in FINANCIAL_TOOLS}
        elif self.task == "news":
            self.tools = {tool['name']: tool for tool in NEWS_TOOLS}
        elif self.task == "fundamental":
            self.tools = {}
    
    def _create(self, contents: list, schema: BaseModel=None, deep: bool=False):
        model = self.deep_model if deep else self.quick_model
        thinking_budget = self.deep_thinking_budget if deep else self.quick_thinking_budget

        system_instruction = None

        return self.llm_client.generate_content(
            model=model,
            contents=contents,
            system_instruction=system_instruction,
            thinking_budget=thinking_budget,
            schema=schema,
        )
    
    def _analysis(self, context: Context):
        res = self._create(
            contents=self.history,
            schema=AnalysisSchema,
            deep=True
        )

        self.todo_next = res.content.get("todo_next", "")
        self._add_history(
            "--- ANALYSIS RESULT ---\n" +\
            f"REASONING: {res.content.get('reasoning')}\n" +\
            f"SUMMARY: {res.content.get('summary')}\n" +\
            f"TODO/NEXT: {self.todo_next}\n",
            context
        )
    
    def _call_tool(self, tool_name: str, parameters: dict):
        tool_func = self.tools.get(tool_name).get('func')
        if not tool_func:
            raise ValueError(f"Tool {tool_name} not found.")

        return tool_func(**parameters)
    
    def _get_context_parameters(self, tool_name: str, context: Context) -> dict:
        return {
            key: context.get_cache(value, "")
            for key, value
            in self.tools[tool_name]['context_params'].items()
        }
    
    def _use_tool(self, tool_name: str, params: dict, context: Context) -> str:
        all_params = {**params, **self._get_context_parameters(tool_name, context)}

        tool_result = self._call_tool(tool_name, all_params)
        return  "--- TOOL RESULT ---\n" +\
                f"TOOL NAME: {tool_name}\n" +\
                f"PARAMETERS: {all_params}\n" +\
                f"RESULT: {tool_result}\n"
    
    def _use_tools(self, context: Context):
        ToolListSchema = get_tool_schema(self.tools)
        res = self._create(
            contents=self.history,
            schema=ToolListSchema,
        )

        _history =  "--- TOOL USAGE ---\n" +\
                    f"REASONING: {res.content.get('reasoning')}\n"
        
        for tool in res.content.get("tools"):
            tool_name = tool.get("tool_name")
            params = {x['parameter_name']: x['value'] for x in tool.get("params", [])}
            params = {k: v for k, v in params.items() if k in self.tools[tool_name]['params']}
            self._use_tool(tool_name, params, context)
            _history += f"\n{self._use_tool(tool_name, params, context)}\n"
        
        self._add_history(_history, context)



    def _make_report(self, context: Context) -> Context:
        res = self._create(
            contents=self.history,
            schema=ReportSchema,
            deep=True
        )
        ticker = context.get_cache("ticker", "")
        date = context.get_cache("date", "20251101T0000")
        context.set_report(ticker, date, self.task, res.content)
        context.add_log(
            summary=f"{ticker} - {self.task} 분석 보고서 생성",
            content=context.get_report(ticker, date, self.task),
        )

    def run(self, context: Context) -> Context:
        if len(self.history) == 0:
            ticker = context.get_cache("ticker", "")
            self._add_history(
                f"You are {self.task} analyst for {ticker}. You need to analyze the data and provide insights.\n" +\
                "If you don't have enough information, plan to use tools to gather more data.\n" +\
                "Available tools:\n" +\
                "\n".join([f"{tool['name']}: {tool['desc']}" for tool in self.tools.values()]) + "\n",
                context
            )
        
        self._analysis(context)
        
        if self.todo_next:
            self._use_tools(context)
            return context
        
        self._make_report(context)
        return context