import asyncio
import json
from dedalus_labs import AsyncDedalus
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
from typing import List, Optional, Any, Dict
import contextlib
import sys
import json
import os
import subprocess
import asyncio

from mcp import ClientSession
from mcp.client.sse import sse_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# --- Pydantic Models ---
class QuestionNode(BaseModel):
    text: str
    level: int
    children: List["QuestionNode"] = Field(default_factory=list)
    answer: Optional[str] = None
    probability_score: Optional[float] = None

QuestionNode.model_rebuild()


class Question(BaseModel):
    question_one: str
    question_two: str
    question_three: str
    question_four: str
    question_five: str

class AnswerWithScore(BaseModel):
    answer: str
    score: float = Field(description="Probability score between 0.0 and 1.0 indicating how strongly the answer supports a 'Yes' to the original question, based on the evidence.")


# --- Generate 5 Subquestions ---
async def generate_five_questions(client, question: str) -> List[str]:
    completion = await client.chat.completions.parse(
        model="openai/gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"""
                Generate exactly 5 atomic, factual subquestions to help answer:

                '{question}'

                Ensure that if these subquestions are evaluated as 'True' or have a high probability, they support a 'Yes' answer to the original question.

                Return JSON:
                question_one, question_two, question_three, question_four, question_five
                """
            }
        ],
        response_format=Question,
    )

    parsed: Question = completion.choices[0].message.parsed

    return [
        parsed.question_one,
        parsed.question_two,
        parsed.question_three,
        parsed.question_four,
        parsed.question_five,
    ]

def save_tree_to_json(tree: QuestionNode, filename: str = "questions.json"):
    json_data = tree.model_dump()  # fully serializable dict
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)
    print(f"Saved tree to {filename}")

# --- RECURSIVE EXPANSION (THIS CREATES 1 → 5 → 25 → 125) ---
async def expand_node(client, node: QuestionNode, max_depth: int):
    # Stop condition
    if node.level >= max_depth:
        return

    # Generate 5 children
    subquestions = await generate_five_questions(client, node.text)

    for q in subquestions:
        child = QuestionNode(
            text=q,
            level=node.level + 1
        )
        node.children.append(child)

        # Expand each child
        await expand_node(client, child, max_depth)


# --- Build Full Tree ---
async def build_question_tree(main_question: str):
    client = AsyncDedalus()

    root = QuestionNode(text=main_question, level=0)

    # max_depth = 3 means:
    # level 0 generates level 1
    # level 1 generates level 2
    # level 2 generates level 3
    # level 3 stops.
    await expand_node(client, root, max_depth=3)

    return root


# --- MCP Integration ---

@contextlib.asynccontextmanager
async def run_mcp_server():
    # Start the FastAPI server as a subprocess
    print("Starting MCP server on port 8000...")
    proc = subprocess.Popen(
        ["python", "mcp/server.py"],
        env=os.environ,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Wait for server to start
    # In a robust implementation, we'd poll the health endpoint
    await asyncio.sleep(5)
    
    try:
        # Connect via SSE
        # FastMCP typically exposes SSE at /sse
        async with sse_client("http://localhost:8000/sse") as (read, write):
            async with ClientSession(read, write) as session:
                yield session
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")
        raise
    finally:
        print("Stopping MCP server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

def convert_mcp_tool_to_openai(mcp_tool: Any) -> Dict[str, Any]:
    """Convert an MCP tool definition to OpenAI's function format."""
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema
        }
    }

async def answer_question_with_mcp(client: AsyncDedalus, mcp_session: ClientSession, question: str) -> AnswerWithScore:
    """
    Uses the LLM to answer a question by calling tools available on the MCP server.
    Returns an answer and a probability score.
    """
    # 1. List available tools
    tools_result = await mcp_session.list_tools()
    openai_tools = [convert_mcp_tool_to_openai(tool) for tool in tools_result.tools]
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to NBA data. Use the available tools to answer the user's question accurately. If you cannot find the answer with the tools, say so. Finally, you will be asked to score your confidence that the answer supports a 'Yes' to the original hypothesis."},
        {"role": "user", "content": question}
    ]

    # 2. Loop: Call LLM -> Call Tool -> Repeat until answer
    for _ in range(5): # Max 5 turns to prevent infinite loops
        response = await client.chat.completions.create(
            model="openai/gpt-4o", # Use a strong model for tool calling
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        # Manually construct dict to avoid extra fields that might confuse the API
        msg_dict = {
            "role": message.role,
            "content": message.content
        }
        if message.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]
        messages.append(msg_dict)

        if not message.tool_calls:
            # Final response is text. Now parse it into AnswerWithScore.
            # We append a request to format the output.
            parsing_messages = messages + [{
                "role": "user", 
                "content": "Based on the above, provide the final answer and a probability score (0.0 to 1.0) indicating how strongly this answer supports a 'Yes' outcome for the original question. 1.0 means definitely Yes, 0.0 means definitely No/Irrelevant."
            }]
            
            final_response = await client.chat.completions.parse(
                model="openai/gpt-4o",
                messages=parsing_messages,
                response_format=AnswerWithScore
            )
            return final_response.choices[0].message.parsed

        # Process tool calls
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # print(f"Calling tool: {tool_name} with {tool_args}")
            
            try:
                result = await mcp_session.call_tool(tool_name, tool_args)
                # MCP CallToolResult has 'content' list
                tool_output = ""
                for content in result.content:
                    if content.type == "text":
                        tool_output += content.text
                    # Handle other types if needed
                
            except Exception as e:
                tool_output = f"Error calling tool {tool_name}: {str(e)}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })
            
    return AnswerWithScore(answer="I was unable to answer the question after multiple attempts.", score=0.0)

# --- Tree Processing ---

async def process_tree(root: QuestionNode):
    """
    Traverses the tree and answers each question using MCP.
    """
    client = AsyncDedalus()
    
    async with run_mcp_server() as mcp_session:
        # Initialize MCP session (optional, but good practice if needed)
        await mcp_session.initialize()
        
        # Traverse (BFS)
        queue = [root]
        while queue:
            node = queue.pop(0)
            
            print(f"Answering: {node.text}")
            result = await answer_question_with_mcp(client, mcp_session, node.text)
            node.answer = result.answer
            node.probability_score = result.score
            print(f"Answer: {result.answer[:100]}... (Score: {result.score})")
            
            queue.extend(node.children)

# --- Debug Count ---
def count_levels(root: QuestionNode):
    from collections import Counter
    counter = Counter()

    def dfs(node):
        counter[node.level] += 1
        for c in node.children:
            dfs(c)

    dfs(root)
    return counter



# --- Main ---
async def main():
    question = input("Enter a question: ")
    # tree = await build_question_tree(question)
    
    # For testing, let's build a small tree or load one
    # If we want to build a new one:
    print("Building question tree...")
    tree = await build_question_tree(question)
    
    print("Answering questions with MCP...")
    await process_tree(tree)
    
    save_tree_to_json(tree, "nba_question_tree.json")
    
    print(tree.model_dump())
    print("\nLEVEL COUNTS:")
    print(count_levels(tree))


if __name__ == "__main__":
    asyncio.run(main())
