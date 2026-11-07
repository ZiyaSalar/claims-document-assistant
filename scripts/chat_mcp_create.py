
import asyncio
import json
import os

from dotenv import load_dotenv
from mcp import Client
from mcp.types import TextContent
from openai import OpenAI

from backend.app.mcp.server import mcp

load_dotenv(".env")

DRAFT_TOOL = {
    "type": "function",
    "function": {
        "name": "draft_claim",
        "description": (
            "Extract proposed claim fields from a user's request. "
            "This does not create a claim."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "claimant_name": {"type": "string"},
                "policy_number": {"type": "string"},
                "claim_type": {"type": "string"},
            },
            "required": [
                "claimant_name",
                "policy_number",
                "claim_type",
            ],
            "additionalProperties": False,
        },
    },
}


async def main():
    ai = OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )

    print("Claims Assistant — Confirmed Claim Creation")
    print("Type 'exit' to quit.")

    async with Client(mcp) as client:
        while True:
            request = input("\nYou: ").strip()

            if request.lower() in {"exit", "quit"}:
                break

            if not request:
                continue

            response = ai.chat.completions.create(
                model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract the claim fields provided by the user. "
                            "Do not invent missing information. "
                            "Use empty strings for unspecified fields. "
                            "Do not create any claim."
                        ),
                    },
                    {"role": "user", "content": request},
                ],
                tools=[DRAFT_TOOL],
                tool_choice={
                    "type": "function",
                    "function": {"name": "draft_claim"},
                },
            )

            calls = response.choices[0].message.tool_calls

            if not calls:
                print("Could not extract claim details.")
                continue

            draft = json.loads(calls[0].function.arguments)

            fields = [
                "claimant_name",
                "policy_number",
                "claim_type",
            ]

            draft = {
                key: str(draft.get(key, "")).strip()
                for key in fields
            }

            if not all(draft.values()):
                missing = [
                    key for key, value in draft.items()
                    if not value
                ]
                print("Missing fields:", ", ".join(missing))
                continue

            print("\nProposed claim:")
            print(json.dumps(draft, indent=2))

            confirmation = input(
                "\nCreate this claim? Type CONFIRM: "
            ).strip()

            if confirmation != "CONFIRM":
                print("Cancelled. No claim created.")
                continue

            # The model cannot invoke this tool.
            # Only this explicit confirmation branch can.
            result = await client.call_tool(
                "create_claim",
                draft,
            )

            for block in result.content:
                if isinstance(block, TextContent):
                    print(block.text)

            if result.is_error:
                print("Claim creation failed.")
            else:
                print("Claim creation request completed.")


if __name__ == "__main__":
    asyncio.run(main())
