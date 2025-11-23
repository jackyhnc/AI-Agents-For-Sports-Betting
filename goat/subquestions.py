import asyncio
import json
from dedalus_labs import AsyncDedalus
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()


# --- Pydantic Models ---
class QuestionNode(BaseModel):
    text: str
    level: int
    children: List["QuestionNode"] = Field(default_factory=list)

QuestionNode.model_rebuild()


class Question(BaseModel):
    question_one: str
    question_two: str
    question_three: str
    question_four: str
    question_five: str


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
    tree = await build_question_tree(question)
    save_tree_to_json(tree, "nba_question_tree.json")
    print(tree.model_dump())
    print("\nLEVEL COUNTS:")
    print(count_levels(tree))


if __name__ == "__main__":
    asyncio.run(main())
