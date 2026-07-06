import anthropic

from tests.agentic.agent_runner import DEFAULT_MODEL, AgentRunResult

_JUDGE_SYSTEM = (
    "You are grading whether a shopping agent satisfied a user's purchase instruction. "
    "Respond with exactly one line starting with PASS or FAIL, followed by a "
    "one-sentence reason."
)


async def judge_run(result: AgentRunResult, *, model: str = DEFAULT_MODEL) -> tuple[bool, str]:
    client = anthropic.AsyncAnthropic()
    transcript_summary = "\n".join(
        f"{call.name}({call.input}) -> {call.output}" for call in result.transcript
    )
    prompt = (
        f"User instruction: {result.instruction}\n\n"
        f"Agent's tool calls:\n{transcript_summary}\n\n"
        f"Agent's final message: {result.final_text}\n\n"
        "Did the agent satisfy the user's constraints (product, quantity, budget) and "
        "complete the purchase?"
    )
    response = await client.messages.create(
        model=model,
        max_tokens=200,
        system=_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text.upper().startswith("PASS"), text
