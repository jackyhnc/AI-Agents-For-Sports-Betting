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
from fastmcp.client.transports import StdioTransport
from fastmcp import Client
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn


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
    score: float = Field(
        description="Probability score between 0.0 and 1.0 (Precise as possible to at most the second decimal place) indicating how strongly the answer supports a 'Yes' to the original question, based on the evidence."
    )


class Output(BaseModel):
    reasoning: str
    probability_score: float


# --- FastAPI Request/Response Models ---
class QuestionRequest(BaseModel):
    question: str
    max_depth: int = Field(
        default=1, ge=1, le=3, description="Maximum depth of the question tree (1-3)"
    )


class QuestionResponse(BaseModel):
    tree: dict
    level_counts: dict
    message: str


# --- Generate 5 Subquestions ---
async def generate_five_questions(client, question: str) -> List[str]:
    completion = await client.chat.completions.parse(
        model="openai/gpt-5-nano",
        messages=[
            {
                "role": "user",
                "content": f"""
                Generate exactly 5 atomic, true or false, factual subquestions to help answer:

                '{question}'

                Ensure that if these subquestions are evaluated as 'True' or have a probability closer to 1.0, they support a 'Yes' answer to the original question. If they are 'False' or have a probability closer to 0.0, they support a 'No' answer.

                Return JSON:
                question_one, question_two, question_three, question_four, question_five
                """,
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

    for i, q in enumerate(subquestions, 1):
        child = QuestionNode(text=q, level=node.level + 1)
        node.children.append(child)
        print(f"  [{node.level + 1}.{i}] Created: {q}")

        # Expand each child
        await expand_node(client, child, max_depth)


# --- Build Full Tree ---
async def build_question_tree(main_question: str, max_depth: int):
    client = AsyncDedalus()

    root = QuestionNode(text=main_question, level=0)
    print(f"[Level 0] Root question created: {main_question}")

    # max_depth = 3 means:
    # level 0 generates level 1
    # level 1 generates level 2
    # level 2 generates level 3
    # level 3 stops.
    await expand_node(client, root, max_depth=max_depth)

    return root


# --- MCP Integration ---

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# MCP server URL - can be overridden via environment variable
#### CHANGE HERE BC URL CHANGES
MCP_SERVER_URL = os.environ.get(
    "MCP_SERVER_URL", "https://9227e9b19454.ngrok-free.app/mcp/"
)


async def answer_question_with_mcp(client: Client, question: str) -> AnswerWithScore:
    """
    Answer a question using OpenAI with MCP server integration.
    Uses the same prompt format as test.py for consistency.
    """
    prompt = f"""
    My question is: {question}
    I want to know how strongly the answer is a 'Yes' to the original question, based on evidence.

    ## Before answering, do comprehensive research of all possible factors by using the MCP server provided without needing 
    to ask for permission and then reasoning. You have access to a maximum of 2 tool calls (choose wisely) of your choice to the MCP server.

    ### Your output: 
    Reasoning: Your reasoning that you do from your research.
    Then, the Probability Score: A probability score between 0.0 and 1.0 (Precise as possible to at most the second decimal place) indicating 
    how strongly the answer supports a 'Yes' to the original question, based on the evidence.
    """

    # Run the synchronous OpenAI call in an executor to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: openai_client.responses.parse(
            model="gpt-5-mini",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "nba_server",
                    "server_description": "NBA MCP server to assist with NBA questions.",
                    "server_url": MCP_SERVER_URL,
                    "require_approval": "never",
                },
            ],
            input=prompt,
            text_format=Output,
            max_tool_calls=2,
        ),
    )

    # Debug: check what we actually got
    print(f"DEBUG: resp type: {type(resp)}")
    print(f"DEBUG: resp.output_text type: {type(resp.output_text)}")
    print(f"DEBUG: resp.output_text value: {resp.output_text}")

    # Check if there's a parsed attribute or if output_text needs parsing
    if hasattr(resp, "parsed") and resp.parsed:
        output = resp.parsed
    elif isinstance(resp.output_text, Output):
        output = resp.output_text
    elif isinstance(resp.output_text, str):
        # If it's a string, try to parse it
        output = Output.model_validate_json(resp.output_text)
    else:
        # Try to use it directly
        output = resp.output_text

    return AnswerWithScore(
        answer=output.reasoning,
        score=output.probability_score,
    )


# --- Tree Processing ---


async def process_tree(root: QuestionNode):
    """
    Traverses the tree and answers each question using MCP.
    """
    client = AsyncDedalus()

    # Traverse (BFS)
    queue = [root]
    while queue:
        node = queue.pop(0)

        print(f"Answering: {node.text}")
        result = await answer_question_with_mcp(client, node.text)
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


# --- FastAPI App ---
app = FastAPI(
    title="Question Tree API",
    description="API for building and processing question trees with MCP integration",
    version="1.0.0",
)


@app.post("/process-question", response_model=QuestionResponse)
async def process_question(request: QuestionRequest):
    """
    Process a question by building a question tree and answering all questions.

    - **question**: The main question to process
    - **max_depth**: Maximum depth of the question tree (default: 1, max: 3)
    """
    try:
        print(f"Building question tree for: {request.question}")
        tree = await build_question_tree(request.question, max_depth=request.max_depth)

        print("Answering questions with MCP...")
        await process_tree(tree)

        # Save to JSON file
        save_tree_to_json(tree, "nba_question_tree.json")

        # Get level counts
        level_counts = count_levels(tree)

        return QuestionResponse(
            tree=tree.model_dump(),
            level_counts=dict(level_counts),
            message="Question tree processed successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing question: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# --- Main (Terminal Input) ---
async def main():
    question = input("Enter a question: ")
    # tree = await build_question_tree(question)

    # For testing, let's build a small tree or load one
    # If we want to build a new one:
    print("Building question tree...")
    tree = await build_question_tree(question, max_depth=1)

    print("Answering questions with MCP...")
    await process_tree(tree)

    save_tree_to_json(tree, "nba_question_tree.json")

    print(tree.model_dump())
    print("\nLEVEL COUNTS:")
    print(count_levels(tree))


if __name__ == "__main__":
    import sys

    # If running with --api flag, start FastAPI server
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Otherwise, run the original terminal input version
        asyncio.run(main())
