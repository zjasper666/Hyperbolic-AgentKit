import requests
import json
from typing import Optional

from collections.abc import Callable

from pydantic import BaseModel, Field

from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.utils import get_api_key

GET_GPU_STATUS_PROMPT = """
This tool will get all the the status and ssh commands of my currently rented GPUs on the Hyperbolic platform.

It does not take any inputs

Important notes:
- Authorization key is required for this operation
- The GPU prices are in USD cents per hour
"""


class GetGpuStatusInput(BaseModel):
  """Input argument schema for getting available GPUs."""


def get_gpu_status() -> str:
  """
  Returns a string representation of the response from the Hyperbolic API.
  Returns:
    A string representing the response from the API.
  """
  # Get API key from environment
  api_key = get_api_key()

  url = "https://api.hyperbolic.xyz/v1/marketplace/instances"
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
  }
  response = requests.get(url, headers=headers)
  return response.json()


class GetGpuStatusAction(HyperbolicAction):
  """Get status for my GPUs action."""

  name: str = "get_gpu_status"
  description: str = GET_GPU_STATUS_PROMPT
  args_schema: type[BaseModel] | None = GetGpuStatusInput
  func: Callable[..., str] = get_gpu_status
