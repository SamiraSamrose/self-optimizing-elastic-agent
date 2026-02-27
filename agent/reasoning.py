import json
from config.settings import (
    REASONING_PROVIDER,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from config.tool_schemas import ALL_TOOL_SCHEMAS

#System Prompt
SYSTEM_PROMPT = (
    "You are an expert Elastic SRE Agent. Your goal is to minimize query latency and maximize "
    "resource efficiency. When you detect a performance bottleneck via ES|QL, search the "
    "documentation for the 'Best Practice' resolution. Propose a configuration change or a "
    "re-indexing strategy. Never apply a 'destructive' change without explaining the 'Why' "
    "and seeking approval."
)


def call_reasoning_model(messages: list[dict], tool_results: dict = None) -> dict:
    """
    Calls the configured reasoning model with the current conversation messages.
    Returns either a text response or a tool call the agent should execute.
    """
    if tool_results:
        for tool_name, result in tool_results.items():
            messages.append({
                "role": "user",
                "content": f"Tool result for {tool_name}: {json.dumps(result)}"
            })

    if REASONING_PROVIDER == "anthropic":
        return _call_anthropic(messages)
    elif REASONING_PROVIDER == "openai":
        return _call_openai(messages)
    else:
        raise ValueError(f"Unknown reasoning provider: {REASONING_PROVIDER}")


def _call_anthropic(messages: list[dict]) -> dict:
    """
    Calls Claude 3.5 Sonnet via the Anthropic API with tool use enabled.
    """
    import anthropic

    tools = [
        {
            "name": schema["name"],
            "description": schema["description"],
            "input_schema": schema["parameters"],
        }
        for schema in ALL_TOOL_SCHEMAS
    ]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=messages,
    )

    for block in response.content:
        if block.type == "tool_use":
            return {
                "type": "tool_call",
                "tool_name": block.name,
                "tool_args": block.input,
                "raw": response,
            }

    text = " ".join(
        block.text for block in response.content if hasattr(block, "text")
    )
    return {"type": "text", "content": text, "raw": response}


def _call_openai(messages: list[dict]) -> dict:
    """
    Calls GPT-4o via the OpenAI API (Open Inference API) with function calling.
    """
    from openai import OpenAI

    functions = [
        {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["parameters"],
            }
        }
        for schema in ALL_TOOL_SCHEMAS
    ]

    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=functions,
        tool_choice="auto",
    )

    choice = response.choices[0]
    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        return {
            "type": "tool_call",
            "tool_name": tool_call.function.name,
            "tool_args": json.loads(tool_call.function.arguments),
            "raw": response,
        }

    return {"type": "text", "content": choice.message.content, "raw": response}


def build_initial_message(context: dict) -> list[dict]:
    """
    Builds the initial user message with full telemetry AND the
    structured diagnosis output. The model can immediately see which anti-patterns
    were detected and which Knowledge Tool queries are recommended — no guessing.
    """
    recommended = context.get("top_recommended_searches", [])
    recommended_block = ""
    if recommended:
        recommended_block = (
            "\n\nDiagnosis-recommended Knowledge Tool queries to run first:\n"
            + "\n".join(f"  - \"{q}\"" for q in recommended)
        )

    content = (
        "A new optimization cycle has started. Here is the current cluster telemetry:\n\n"
        f"Slowest queries (last hour):\n{json.dumps(context.get('slow_queries'), indent=2)}\n\n"
        f"Node metrics:\n{json.dumps(context.get('node_metrics'), indent=2)}\n\n"
        f"Circuit breaker stats:\n{json.dumps(context.get('circuit_breakers'), indent=2)}\n\n"
        f"Structural diagnosis (Step 4.2):\n{context.get('diagnosis', 'No diagnosis available.')}"
        f"{recommended_block}\n\n"
        "Using the diagnosis above, run the recommended Knowledge Tool queries to research "
        "the best-practice fixes. Then propose an optimization plan (Step A: create template, "
        "Step B: reindex, Step C: update alias). Do not apply any destructive change without "
        "stating the reason and seeking approval."
    )
    return [{"role": "user", "content": content}]
