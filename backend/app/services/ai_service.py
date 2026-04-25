import os

from openai import OpenAI

from .response_style import CONVERSATIONAL_SYSTEM_PROMPT, build_constraint_context, format_conversational_response


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_ai_reply(
    message: str,
    conversation_history: list[dict[str, str]] | None = None,
    user_memory: str | None = None,
):
    try:
        messages = [
            {"role": "system", "content": CONVERSATIONAL_SYSTEM_PROMPT},
        ]

        constraint_context = build_constraint_context(message)
        if constraint_context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Hard requirements. You MUST use every exact user constraint in the final answer when relevant. If the user gave exact values like $40, 3 hours, tomorrow afternoon, or 9am-12pm, those exact values must appear in the user-facing answer. Do not replace them with broader wording. If a sentence violates the constraints, replace it with a cheaper, faster, internal-only alternative instead: "
                        f"{constraint_context}"
                    ),
                }
            )

        if user_memory:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Private user context for reasoning only. Use it only if it is directly relevant to the user's goal or constraints. Do not restate or list these facts unless the user asks or the answer truly depends on them. Do not mention memory, prior disclosures, or phrases like 'from what you told me' or 'I remember that'. Blend relevant facts in naturally only when they improve the answer. Never invent new facts: "
                        f"{user_memory}"
                    ),
                }
            )

        for item in (conversation_history or [])[-10:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})

        prompt_messages = [
            {"role": item.get("role"), "content": item.get("content")}
            for item in messages
            if item.get("role") in {"user", "assistant"}
        ]
        print(
            "[CHAT DEBUG] final_ai_messages="
            f"{len(prompt_messages)} tail={prompt_messages[-3:]}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )

        return {
            "reply": format_conversational_response(response.choices[0].message.content or "")
        }

    except Exception as e:
        return {"error": str(e)}