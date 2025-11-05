from pydantic import BaseModel

class BullReply(BaseModel):
    chat: str

class BearReply(BaseModel):
    chat: str

class ManagerDecision(BaseModel):
    decision: str  # "BUY" | "SELL" | "HOLD"
    rationale: str
    plan: str
