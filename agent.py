"""
ReAct Tool-calling Agent using Claude's native tool_use API.

The ReAct loop (Reasoning + Acting):
  1. User question → Claude + tool schemas
  2. Claude emits tool_use blocks (reasoning about which tools to call)
  3. We execute each tool and return tool_result blocks
  4. Claude reasons again with new observations
  5. Repeat until stop_reason == "end_turn" (Claude has enough to answer)

This implements Function Calling from scratch — no LangChain agent abstraction —
so the tool schema design and execution loop are fully visible and controllable.
"""

import os
from dotenv import load_dotenv
import anthropic

from tools import TOOL_SCHEMAS, TOOL_MAP

load_dotenv()

SYSTEM = (
    "You are a research assistant with access to a private document knowledge base. "
    "Use the available tools to answer questions accurately. "
    "Always cite the source file and page number when drawing from documents. "
    "If a question requires multiple tool calls, make them — do not guess. "
    "If the documents do not contain the answer, say so clearly."
)

client = anthropic.Anthropic()


def run(question: str, verbose: bool = True) -> str:
    """Run the agent on a question, returning the final answer."""
    messages = [{"role": "user", "content": question}]
    step = 0

    while True:
        step += 1
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if verbose:
            print(f"\n[Step {step}] stop_reason={response.stop_reason}")

        # ── Claude finished — extract and return text answer ───────────────
        if response.stop_reason == "end_turn":
            return next(
                (block.text for block in response.content if hasattr(block, "text")),
                "(no text response)"
            )

        # ── Claude wants to call tools ─────────────────────────────────────
        if response.stop_reason == "tool_use":
            # Append Claude's response (including tool_use blocks) to history
            messages.append({"role": "assistant", "content": response.content})

            # Execute every tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if verbose:
                    print(f"  -> Tool: {block.name}  Input: {block.input}")

                try:
                    result = TOOL_MAP[block.name](block.input)
                except Exception as exc:
                    result = f"Tool error: {exc}"

                if verbose:
                    preview = result[:120].replace("\n", " ").encode("ascii", errors="replace").decode()
                    print(f"  <- Result: {preview}{'...' if len(result) > 120 else ''}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            # Feed all results back to Claude in a single user turn
            messages.append({"role": "user", "content": tool_results})
            continue

        # ── Unexpected stop reason ─────────────────────────────────────────
        break

    return "(agent loop exited unexpectedly)"


if __name__ == "__main__":
    demo_questions = [
        "What documents are indexed and how many chunks total?",
        "What are the eligibility criteria for stem cell donation?",
        "Summarise the key transplant outcome findings. Also, what is today's date?",
    ]

    for q in demo_questions:
        print(f"\n{'='*64}")
        print(f"Q: {q}")
        print("=" * 64)
        answer = run(q, verbose=True)
        print(f"\nFinal answer:\n{answer}")
