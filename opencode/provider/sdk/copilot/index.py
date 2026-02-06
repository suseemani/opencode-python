"""GitHub Copilot SDK integration."""

from typing import Any, AsyncIterator

from pydantic import BaseModel, Field

from opencode.util import create as create_logger

log = create_logger({"service": "provider", "sdk": "copilot"})


class CopilotConfig(BaseModel):
    """Copilot SDK configuration."""
    
    api_key: str | None = Field(default=None, description="Copilot API key")
    endpoint: str = Field(default="https://api.github.com/copilot", description="API endpoint")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class CopilotCompletionRequest(BaseModel):
    """Copilot completion request."""
    
    prompt: str = Field(description="Code prompt")
    language: str = Field(default="python", description="Programming language")
    max_tokens: int = Field(default=100, description="Maximum tokens to generate")
    temperature: float = Field(default=0.2, description="Temperature")


class CopilotCompletion(BaseModel):
    """Copilot completion response."""
    
    text: str = Field(description="Generated completion")
    language: str = Field(description="Language")
    confidence: float = Field(default=1.0, description="Completion confidence")


class CopilotSDK:
    """GitHub Copilot SDK client."""
    
    def __init__(self, config: CopilotConfig | None = None) -> None:
        self.config = config or CopilotConfig()
        self._client = None
    
    def _get_client(self):
        """Get or create HTTP client."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint,
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Accept": "application/json",
                } if self.config.api_key else {},
            )
        return self._client
    
    async def complete(
        self,
        request: CopilotCompletionRequest,
    ) -> AsyncIterator[CopilotCompletion]:
        """Get code completion from Copilot."""
        client = self._get_client()
        
        try:
            response = await client.post(
                "/completions",
                json={
                    "prompt": request.prompt,
                    "language": request.language,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Yield completions
            for choice in data.get("choices", []):
                yield CopilotCompletion(
                    text=choice.get("text", ""),
                    language=request.language,
                )
        
        except Exception as e:
            log.error("Copilot completion failed", {"error": str(e)})
            raise
    
    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Chat with Copilot."""
        client = self._get_client()
        
        try:
            response = await client.post(
                "/chat/completions",
                json={
                    "messages": messages,
                    "stream": stream,
                },
            )
            
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        # Parse and yield content
                        yield data
            else:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                yield content
        
        except Exception as e:
            log.error("Copilot chat failed", {"error": str(e)})
            raise
    
    async def check_auth(self) -> bool:
        """Check if authentication is valid."""
        if not self.config.api_key:
            return False
        
        try:
            client = self._get_client()
            response = await client.get("/user")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close the client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Convenience function
def create_client(api_key: str | None = None) -> CopilotSDK:
    """Create a Copilot SDK client."""
    config = CopilotConfig(api_key=api_key)
    return CopilotSDK(config)
