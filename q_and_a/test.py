import os
import dotenv
from pydantic import BaseModel

dotenv.load_dotenv()
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

question = "Will Philadelphia win the Miami Heat vs Philadelphia 76ers game?"
prompt = f"""
    My question is: {question}
    I want to know how strongly the answer is a 'Yes' to the original question, based on evidence.

    ## Before answering, do comprehensive research of all possible factors by using the MCP server provided without needing 
    to ask for permission and then reasoning. You have access to a maximum of 2 tool calls (choose wisely) of your choice (choose wisely) to the MCP server.

    ### Your output: 
    Reasoning: Your reasoning that you do from your research.
    Then, the Probability Score: A probability score between 0.0 and 1.0 (Precise as possible to at most the second decimal place) indicating 
    how strongly the answer supports a 'Yes' to the original question, based on the evidence.
"""


class Output(BaseModel):
    reasoning: str
    probability_score: float


resp = client.responses.parse(
    model="gpt-5-nano",
    tools=[
        {
            "type": "mcp",
            "server_label": "nba_server",
            "server_description": "NBA MCP server to assist with NBA questions.",
            "server_url": "https://9227e9b19454.ngrok-free.app/mcp/",
            "require_approval": "never",
        },
    ],
    input=prompt,
    text_format=Output,
    max_tool_calls=2,
)

print("--------------------------------")
print(resp.output_text)
