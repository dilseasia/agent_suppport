from app.services.tools import appointment, dealership, weather
from .schema import SupportRequest, SupportResponse
from .prompt import SUPPORT_PROMPT
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# -------------------------
# Tools registry
# -------------------------from app.services.tools import appointment, dealership, weather
from .schema import SupportRequest, SupportResponse
from .prompt import SUPPORT_PROMPT
from langchain_groq import ChatGroq

# -------------------------
# Tools registry (handle functions directly)
# -------------------------
TOOLS = {
    "appointment": appointment.handle,
    "dealership": dealership.handle,
    "weather": weather.handle,
}

# -------------------------
# Intent router
# -------------------------
def route_query(query: str) -> str | None:
    q = query.lower()
    if "appointment" in q or "book" in q or "cancel" in q:
        return "appointment"
    elif "dealer" in q or "car" in q or "vehicle" in q:
        return "dealership"
    elif "weather" in q or "temperature" in q or "rain" in q or "forecast" in q:
        return "weather"
    return None

# -------------------------
# LLM Wrapper
# -------------------------
class GroqLLM:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model=self.model,
            temperature=0.7,
            max_tokens=300,
        )
        print(f"Device set to use Groq LLM, model: {self.model}")

    def generate(self, prompt: str) -> str:
        try:
            resp = self.llm.invoke(prompt)
            return resp.content.strip()
        except Exception as e:
            return None  # fail hone pe None return

# -------------------------
# Support Agent
# -------------------------
class SupportAgent:
    def __init__(self):
        # Directly passing API key and model here
        self.llm = GroqLLM(
            api_key="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",
            model="openai/gpt-oss-20b"
        )
        print("Support Agent initialized with Groq LLM")
        self.prompt = SUPPORT_PROMPT
        self.fallback_msg = "Sorry, I don’t have information about that right now. Please try again later."

    def handle_request(self, request: SupportRequest, thread_id: str = None) -> SupportResponse:
        tool_name = route_query(request.message)
        tool_output = None

        if tool_name and tool_name in TOOLS:
            tool_output = TOOLS[tool_name](request.message)

        llm_prompt = f"""{self.prompt}
    User query: "{request.message}"
    Tool output: {tool_output}
    Respond naturally and concisely."""

        reply = self.llm.generate(llm_prompt)

        if not reply:
            reply = self.fallback_msg

        return SupportResponse(
            response=reply,
            tool_used=tool_name,
            tool_output=tool_output,
            error_message=None if reply else "LLM failed",
        )
