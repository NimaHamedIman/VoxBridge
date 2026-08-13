"""
Tool registry for VoxBridge. Knows only about memory.py — no groq,
no ai_engine, so the AI backend can be swapped without touching this file.
"""
from memory import save_fact

# user_key is deliberately absent from the schema: the model fills schema
# parameters from user-controlled text, so an identity field here would
# let one user's words address another user's memory. user_key is passed
# in by the caller from server-side session state, never by the model.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "erinnere_dich",
            "description": (
                "Store a durable personal detail about the user that should be "
                "remembered across future conversations - things like their name, "
                "pets, job, preferences, or important dates. Do NOT call this for "
                "passing remarks, for anything already established earlier in the "
                "current conversation, or for instructions about how to behave or "
                "respond. Example: the user mentions they have two cats -> call "
                "this with a short fact stating that."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fakt": {
                        "type": "string",
                        "description": (
                            "The fact as a short third-person statement, e.g. "
                            '"Nima hat zwei Katzen".'
                        ),
                    }
                },
                "required": ["fakt"],
                "additionalProperties": False,
            },
        },
    }
]


def _erinnere_dich(arguments: dict, user_key: str) -> str:
    return save_fact(user_key, arguments.get("fakt", ""))


TOOL_REGISTRY = {
    "erinnere_dich": _erinnere_dich,
}


def dispatch(name: str, arguments: dict, user_key: str) -> str:
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        return f"The tool '{name}' does not exist."

    # The model can call with malformed arguments or the tool can hit a DB
    # error; either way this result is fed straight back into the model's
    # context as the tool response, so a failure must come back as a
    # sentence it can speak, not as an exception that kills the request.
    try:
        return tool(arguments, user_key)
    except Exception as e:
        print(f"Tool '{name}' failed: {e}")
        return "Something went wrong while saving that, sorry."
