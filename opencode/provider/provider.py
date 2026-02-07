"""AI Provider for OpenCode with big-pickle model only."""

import json
import os
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
from pydantic import BaseModel, Field

from opencode.util.http import get_proxy_config, should_use_proxy


class Model(BaseModel):
    """An AI model definition."""

    id: str = Field(description="Model ID")
    name: str = Field(description="Model name")
    provider: str = Field(description="Provider type")
    max_tokens: int = Field(description="Maximum context length")
    supports_vision: bool = Field(default=False, description="Whether model supports vision")
    supports_tools: bool = Field(default=True, description="Whether model supports tools")


class Message(BaseModel):
    """A message for LLM completion."""

    role: str = Field(description="Message role: system, user, assistant")
    content: str = Field(description="Message content")


class CompletionRequest(BaseModel):
    """Request for LLM completion."""

    model: str = Field(description="Model ID")
    messages: list[Message] = Field(description="Conversation messages")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None)
    stream: bool = Field(default=True)


class CompletionChunk(BaseModel):
    """A chunk of a streaming completion."""

    content: str | None = Field(default=None, description="Text content")
    tool_call: dict[str, Any] | None = Field(default=None, description="Tool call delta")
    finish_reason: str | None = Field(default=None, description="Finish reason if done")


class OpenCodeProvider:
    """OpenCode provider with big-pickle model - supports both cloud and local models."""

    type = "opencode"
    
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        use_config: bool = True
    ) -> None:
        self._config_base_url = None
        self._config_api_key = None
        
        # Try to load from config if requested
        if use_config:
            self._load_config()
        
        # Use provided values or fallbacks
        # Priority: 1) Constructor args, 2) Config file, 3) Env vars, 4) Defaults
        self.base_url = base_url or self._config_base_url or os.environ.get("OPENCODE_API_URL") or "https://opencode.ai/zen/v1"
        self.api_key = api_key or self._config_api_key or os.environ.get("OPENCODE_API_KEY")
        self._client: httpx.AsyncClient | None = None
        
        print(f"[OpenCodeProvider] Using endpoint: {self.base_url}")
        if self.is_local():
            print(f"[OpenCodeProvider] Local mode detected")
    
    def _load_config(self) -> None:
        """Load configuration from opencode.json."""
        try:
            # Find config file
            cwd = Path.cwd()
            config_file = None
            
            for directory in [cwd] + list(cwd.parents):
                for filename in ["opencode.json", "opencode.jsonc"]:
                    candidate = directory / filename
                    if candidate.exists():
                        config_file = candidate
                        break
                if config_file:
                    break
            
            if not config_file:
                # Try global config
                global_config = Path.home() / ".config" / "opencode" / "opencode.json"
                if global_config.exists():
                    config_file = global_config
            
            if config_file and config_file.exists():
                print(f"[OpenCodeProvider] Loading config from: {config_file}")
                with open(config_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Remove comments for jsonc
                    if config_file.suffix == ".jsonc":
                        lines = content.split("\n")
                        content = "\n".join(line for line in lines if not line.strip().startswith("//"))
                    
                    data = json.loads(content)
                    
                    # Get opencode provider config
                    provider_config = data.get("provider", {}).get("opencode", {})
                    options = provider_config.get("options", {})
                    
                    # Extract base URL (endpoint takes precedence)
                    self._config_base_url = options.get("endpoint") or options.get("baseURL")
                    if self._config_base_url:
                        print(f"[OpenCodeProvider] Config baseURL: {self._config_base_url}")
                    
                    # Extract API key
                    self._config_api_key = options.get("apiKey")
                    
        except Exception as e:
            print(f"[OpenCodeProvider] Config loading failed: {e}")
            pass
    
    def is_local(self) -> bool:
        """Check if using a local model endpoint."""
        return (
            "localhost" in self.base_url or 
            "127.0.0.1" in self.base_url or 
            self.base_url.startswith("http://")
        )
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Get proxy configuration from environment
            proxy_config = get_proxy_config()
            
            client_kwargs = {
                "base_url": self.base_url,
                "headers": headers,
                "timeout": 120.0,
                "follow_redirects": True,
            }
            
            # Add proxy if configured
            if proxy_config:
                # Remove no_proxy from proxy_config as it's handled separately
                no_proxy_hosts = proxy_config.pop("no_proxy", None)
                
                if proxy_config:
                    # Check if base_url is in no_proxy list
                    if should_use_proxy(self.base_url, no_proxy_hosts):
                        # Use the HTTPS proxy if available, otherwise HTTP proxy
                        proxy_url = proxy_config.get("https://") or proxy_config.get("http://")
                        if proxy_url:
                            client_kwargs["proxy"] = proxy_url
                            print(f"[OpenCodeProvider] Using proxy: {proxy_url}")
                    else:
                        print(f"[OpenCodeProvider] Proxy configured but {self.base_url} is in NO_PROXY")
            
            self._client = httpx.AsyncClient(**client_kwargs)
        return self._client
    
    async def complete(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        """Generate completion by calling the OpenCode API or local model."""
        client = self._get_client()
        
        # Prepare the request payload (OpenAI-compatible format)
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": request.stream,
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        try:
            if request.stream:
                # Streaming response
                async with client.stream(
                    "POST",
                    "/chat/completions",
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(f"API Error {response.status_code}: {error_text.decode()}")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            
                            try:
                                chunk_data = json.loads(data)
                                choice = chunk_data.get("choices", [{}])[0]
                                delta = choice.get("delta", {})
                                finish_reason = choice.get("finish_reason")
                                
                                # Get content from either 'content' or 'reasoning_content'
                                content = delta.get("content") or delta.get("reasoning_content")
                                
                                yield CompletionChunk(
                                    content=content,
                                    finish_reason=finish_reason,
                                )
                            except json.JSONDecodeError:
                                continue
            else:
                # Non-streaming response
                response = await client.post("/chat/completions", json=payload)
                
                if response.status_code != 200:
                    raise Exception(f"API Error {response.status_code}: {response.text}")
                
                data = response.json()
                choice = data.get("choices", [{}])[0]
                
                yield CompletionChunk(
                    content=choice.get("message", {}).get("content"),
                    finish_reason=choice.get("finish_reason"),
                )
                
        except httpx.ConnectError as e:
            if self.is_local():
                raise Exception(
                    f"Cannot connect to local model at {self.base_url}. "
                    f"Is your local model server running?\n"
                    f"Try: ollama serve\n"
                    f"Or check your opencode.json configuration."
                )
            else:
                raise Exception(f"Cannot connect to OpenCode API at {self.base_url}. Please check your internet connection.")
        except httpx.HTTPStatusError as e:
            error_msg = f"API Error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_msg = f"API Error: {error_data['error']}"
            except:
                error_msg = f"API Error: {e.response.text}"
            raise Exception(error_msg)
        except Exception as e:
            if "API Error" not in str(e) and "Cannot connect" not in str(e):
                raise Exception(f"Request failed: {e}")
            raise
    
    def list_models(self) -> list[Model]:
        """List available models - only big-pickle."""
        return [
            Model(
                id="big-pickle",
                name="Big Pickle",
                provider="opencode",
                max_tokens=200000,
                supports_vision=False,
                supports_tools=True,
            ),
        ]


class ProviderManager:
    """Manages AI providers."""

    def __init__(self) -> None:
        self._provider = OpenCodeProvider()

    def get(self, provider_type: str) -> OpenCodeProvider | None:
        """Get the provider."""
        if provider_type == "opencode":
            return self._provider
        return None

    def get_by_model(self, model_id: str) -> OpenCodeProvider | None:
        """Get the provider for a model ID."""
        if model_id == "big-pickle":
            return self._provider
        return None

    def list_models(self) -> list[Model]:
        """List all available models."""
        return self._provider.list_models()


# Global instance
_manager: ProviderManager | None = None


def get_manager() -> ProviderManager:
    """Get the global provider manager."""
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager
