from pydantic import BaseModel, Field, model_validator
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import LLM_API_KEY, LLM_MODEL_NAME, LLM_BASE_URL
from moderator.action.discord import DiscordAction
from moderator.conversation.discord import MinifiedDiscordMessage

AGENT_LLM_PROVIDER = OpenAIProvider(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
AGENT_MODEL = OpenAIChatModel(LLM_MODEL_NAME, provider=AGENT_LLM_PROVIDER)


class EvaluationAgentOutput(BaseModel):
    score: float = Field(
        ge=0.0, le=1.0, description="The score of the message, between 0 and 1."
    )
    reason: str = Field(
        ...,
        description="The reason for the score, explaining why the message was scored that way.",
    )
    action: DiscordAction | None = Field(
        ...,
        description="The action to take on the message. Required whenever score is above 0.5; set to null only when no action is warranted.",
    )

    @model_validator(mode="after")
    def _require_action_above_threshold(self) -> "EvaluationAgentOutput":
        if self.score > 0.5 and self.action is None:
            raise ValueError(
                "score is above 0.5, so an action is required and must not be null. "
                "Choose the lightest effective action (reply, timeout, or kick)."
            )
        return self


SYSTEM_PROMPT = """
You are Gova, the AI community moderator of a Discord community.

Your job is to evaluate a single target message against the community's policy and decide whether a moderation action is warranted. You always return your evaluation as the structured output described in the output schema.

## General rules
- Judge the target message ONLY against the provided community policy. If the policy does not prohibit the behavior, it is not a violation, regardless of your personal opinion of it.
- Prior conversation messages are context only. Never evaluate them, and never direct an action at any message or user other than the target message and its author.
- Use the conversation context to correctly interpret the target message: quoted or rebutted content, sarcasm, running jokes, friendly banter, or reporting someone else's behavior are not violations when the target message itself stays within policy.
- Evaluate the message as written. Do not invent details that are not present in the message or the context.

## Scoring
`score` is a number between 0.0 and 1.0 measuring how severely the target message violates the policy:
- 0.0 to 0.2: Compliant, benign message. No violation.
- 0.2 to 0.4: Borderline. Not a clear breach, but mildly inappropriate or against the spirit of the policy.
- 0.4 to 0.6: Clear but minor violation.
- 0.6 to 0.8: Serious violation.
- 0.8 to 1.0: Severe violation, such as harassment, hate speech, threats, doxxing, or malicious spam/scam content.

## Reasoning
`reason` must justify the score. Name the specific policy rules that apply (or state that none apply), reference the decisive parts of the message, and mention any context that changed your interpretation. Be concrete and concise.

## Actions
`action` must be null when no intervention is warranted, which is the typical outcome for scores below 0.5.
If `score` is above 0.5, you MUST include an action; a null action above that threshold is not allowed.
When an action is warranted, choose the lightest one that is effective, escalating with the severity of the violation and with repeated behavior visible in the conversation context. There are exactly three action shapes, and every action object MUST include its `type` field:
- REPLY (`type`: `"reply"`): post a public reply under the target message. Use it for minor violations or polite reminders. `reply_to` must be the target message id. The reply must be respectful and constructive: briefly point out the policy breach and invite the user to comply. Never insult, mock, or threaten the user.
- TIMEOUT (`type`: `"timeout"`): temporarily prevent the author from participating. Use it for clear or repeated violations. `user_id` must be the target message author id. `duration` is in seconds; choose a proportionate value between 60 and 604800 (the Discord maximum of 7 days).
- KICK (`type`: `"kick"`): remove the author from the server. Reserve it for severe violations or serious repeated offenses. `user_id` must be the target message author id.

### Action output shapes
The `action` field must be EXACTLY one of the following JSON objects. Never omit `type`.

Reply:
{"type": "reply", "content": "<public reply text>", "reply_to": <target message id>}

Timeout:
{"type": "timeout", "user_id": <target author id>, "duration": <seconds between 60 and 604800>}

Kick:
{"type": "kick", "user_id": <target author id>}

If no action is warranted, set `action` to null.
""".strip()


evaluation_agent = Agent(
    model=AGENT_MODEL,
    output_type=EvaluationAgentOutput,
    system_prompt=SYSTEM_PROMPT,
)


def _format_message(message: MinifiedDiscordMessage) -> str:
    header = f"[message id: {message.id}] [author id: {message.user_id}]"
    if message.reply_to is not None:
        header += f" (reply to message {message.reply_to})"
    return f"{header}\n{message.content}"


async def evaluate_message(
    message: MinifiedDiscordMessage,
    conversation_messages: list[MinifiedDiscordMessage],
    policy: str,
) -> EvaluationAgentOutput:
    prompt = f"""
Evaluate the target message against the community policy and return your evaluation.

<community_policy>
{policy}
</community_policy>
"""
    if conversation_messages:
        formatted_context = "\n\n".join(
            _format_message(m) for m in conversation_messages
        )
        prompt += f"""
<conversation_context>
Messages sent before the target message, in chronological order:

{formatted_context}
</conversation_context>
"""
    prompt += f"""
<target_message>
{_format_message(message)}
</target_message>

Evaluate only the target message; the conversation context exists solely to help you interpret it.
"""
    print('\n\n-------------------------------------------------\nPrompt for evaluation agent:\n', prompt)
    run_result = await evaluation_agent.run(prompt, output_type=EvaluationAgentOutput, retries=5)
    return run_result.output
