"""Util that calls Hyperbolic."""

import inspect
import json
from collections.abc import Callable
from typing import Any

from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, model_validator

from hyperbolic_langchain import __version__
from hyperbolic_langchain.constants import HYPERBOLIC_LANGCHAIN_DEFAULT_SOURCE


class HyperbolicAgentkitWrapper(BaseModel):
    """Wrapper for Hyperbolic Agentkit Core."""

    hyperbolic_api_key: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: dict) -> Any:
        """Validate that Hyperbolic API Key exists in the environment."""
        hyperbolic_api_key = get_from_dict_or_env(values, "hyperbolic_api_key", "HYPERBOLIC_API_KEY")
        values["hyperbolic_api_key"] = hyperbolic_api_key
        return values

    def run_action(self, func: Callable[..., str], **kwargs) -> str:
        """Run a Hyperbolic Action."""
        return func(**kwargs)
