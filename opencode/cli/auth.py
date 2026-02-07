"""Authentication management for OpenCode CLI."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from opencode.global_path import get_paths


class AuthCredentials(BaseModel):
    """Authentication credentials for a provider."""
    
    provider: str = Field(description="Provider ID (e.g., openai, anthropic)")
    api_key: str = Field(description="API key")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")
    organization: Optional[str] = Field(default=None, description="Organization ID")


class AuthManager:
    """Manages authentication credentials for API providers."""
    
    def __init__(self) -> None:
        self._credentials: dict[str, AuthCredentials] = {}
        self._load_credentials()
    
    def _get_auth_file(self) -> Path:
        """Get the path to the auth file."""
        paths = get_paths()
        auth_dir = Path(paths.config)
        auth_dir.mkdir(parents=True, exist_ok=True)
        return auth_dir / "auth.json"
    
    def _load_credentials(self) -> None:
        """Load credentials from file."""
        auth_file = self._get_auth_file()
        if auth_file.exists():
            try:
                data = json.loads(auth_file.read_text(encoding="utf-8"))
                for provider, creds in data.items():
                    self._credentials[provider] = AuthCredentials(**creds)
            except (json.JSONDecodeError, Exception):
                # If file is corrupted, start fresh
                self._credentials = {}
    
    def _save_credentials(self) -> None:
        """Save credentials to file."""
        auth_file = self._get_auth_file()
        data = {k: v.model_dump() for k, v in self._credentials.items()}
        auth_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def set_credentials(
        self,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> None:
        """Set credentials for a provider."""
        self._credentials[provider] = AuthCredentials(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            organization=organization,
        )
        self._save_credentials()
    
    def get_credentials(self, provider: str) -> Optional[AuthCredentials]:
        """Get credentials for a provider."""
        return self._credentials.get(provider)
    
    def remove_credentials(self, provider: str) -> bool:
        """Remove credentials for a provider."""
        if provider in self._credentials:
            del self._credentials[provider]
            self._save_credentials()
            return True
        return False
    
    def list_providers(self) -> list[str]:
        """List all providers with credentials."""
        return list(self._credentials.keys())
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider."""
        creds = self._credentials.get(provider)
        return creds.api_key if creds else None


# Global instance
_manager: Optional[AuthManager] = None


def get_manager() -> AuthManager:
    """Get the global auth manager."""
    global _manager
    if _manager is None:
        _manager = AuthManager()
    return _manager


# Supported providers
SUPPORTED_PROVIDERS = [
    ("openai", "OpenAI", "https://platform.openai.com/api-keys"),
    ("anthropic", "Anthropic", "https://console.anthropic.com/settings/keys"),
    ("google", "Google (Gemini)", "https://aistudio.google.com/app/apikey"),
    ("mistral", "Mistral", "https://console.mistral.ai/api-keys/"),
    ("cohere", "Cohere", "https://dashboard.cohere.com/api-keys"),
    ("groq", "Groq", "https://console.groq.com/keys"),
    ("together", "Together AI", "https://api.together.xyz/settings/api-keys"),
    ("openrouter", "OpenRouter", "https://openrouter.ai/settings/keys"),
]
