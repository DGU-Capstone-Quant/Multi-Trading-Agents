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
    
    def _add_history(self, content: str):
        self.history.append(content)
        # for debug:
        print(content + "\n")
    
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
    
    def _analysis(self):
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
            f"TODO/NEXT: {self.todo_next}\n"
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
    
    def _use_tool(self, context: Context):
        ToolSchema = get_tool_schema(self.tools)
        res = self._create(
            contents=self.history,
            schema=ToolSchema,
        )
        tool_name = res.content.get("tool_name", "")
        if tool_name not in self.tools:
            self.history.append(f"--- TOOL USAGE ---\n")
            self.history[-1] += f"Tool {tool_name} not found.\n"
            return

        parameters = {x['parameter_name']: x['value'] for x in res.content.get("parameters", [])}
        parameters = {k: v for k, v in parameters.items() if k in self.tools[tool_name]['params']}
        parameters.update(self._get_context_parameters(tool_name, context))

        tool_result = self._call_tool(tool_name, parameters)
        self._add_history(
            "--- TOOL USAGE ---\n" +\
            f"Used tool: {tool_name}\n" +\
            f"Tool description: {self.tools[tool_name]['desc']}\n" +\
            f"Result: {tool_result}\n"
        )

        # for debug: 
        #print(f"Using tool: {tool_name} with parameters: {parameters}")
        #print(f"Tool result: {tool_result}")

    def _make_report(self, context: Context) -> Context:
        res = self._create(
            contents=self.history,
            schema=ReportSchema,
            deep=True
        )
        context.set_report(self.task, res.content)

    def run(self, context: Context) -> Context:
        if len(self.history) == 0:
            ticker = context.get_cache("ticker", "")
            self._add_history(f"You are {self.task} analyst for {ticker}. You need to analyze the data and provide insights.\n" +\
                            "If you don't have enough information, plan to use tools to gather more data.\n" +\
                            "Available tools:\n" +\
                            "\n".join([f"{tool['name']}: {tool['desc']}" for tool in self.tools.values()]) + "\n")
        
        self._analysis()
        
        if self.todo_next:
            self._use_tool(context)
            return context
        
        self._make_report(context)
        return context