"""Shared helper that runs ONE AutoGen AssistantAgent for ONE task.

A fresh agent (no history) is created per call so only the relevant Kural and
generated content is ever sent to the model.
"""
import warnings
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel

from app.config import Settings

# autogen puts a typed object in a field pydantic expects to be None; harmless log noise
warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)

T = TypeVar("T", bound=BaseModel)


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


class AgentError(Exception):
    pass


# Signature: (name, system_prompt, task, output_model, max_tokens) -> (parsed, usage)
Runner = Callable[[str, str, str, type[T], int], Awaitable[tuple[T, Usage]]]


REVIEW_TEMPERATURE = 0.0  # deterministic, cheaper-to-reason-about reviews
GENERATION_TEMPERATURE = 0.4


class AgentRunner:
    """Callable runner that reuses one OpenAI client per (max_tokens, temperature).

    Clients hold the HTTP connection pool, so reusing them avoids a new TLS
    handshake per call. Agents themselves are cheap and stay stateless: a fresh
    AssistantAgent per call means no conversation history is ever resent.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._clients: dict[tuple[int, float], OpenAIChatCompletionClient] = {}

    def _client(self, max_tokens: int, temperature: float) -> OpenAIChatCompletionClient:
        key = (max_tokens, temperature)
        if key not in self._clients:
            self._clients[key] = OpenAIChatCompletionClient(
                model=self.settings.openai_model, api_key=self.settings.openai_api_key,
                max_tokens=max_tokens, temperature=temperature,
                timeout=self.settings.request_timeout, max_retries=1)
        return self._clients[key]

    async def __call__(self, name: str, system: str, task: str, output_model: type[T], max_tokens: int):
        temperature = REVIEW_TEMPERATURE if name == "review_agent" else GENERATION_TEMPERATURE
        try:
            agent = AssistantAgent(
                name=name, model_client=self._client(max_tokens, temperature), system_message=system,
                output_content_type=output_model, model_client_stream=False)
            result = await agent.run(task=task, cancellation_token=CancellationToken())
            usage = Usage()
            for m in result.messages:
                mu = getattr(m, "models_usage", None)
                if mu:
                    usage.input_tokens += mu.prompt_tokens
                    usage.output_tokens += mu.completion_tokens
            content = result.messages[-1].content
            if not isinstance(content, output_model):
                raise AgentError(f"{name}: unexpected output type")
            return content, usage
        except AgentError:
            raise
        except Exception as e:  # never leak details/secrets upstream
            raise AgentError(f"{name} failed: {type(e).__name__}") from None

    async def aclose(self) -> None:
        for c in self._clients.values():
            await c.close()
        self._clients.clear()


def make_runner(settings: Settings) -> AgentRunner:
    return AgentRunner(settings)
