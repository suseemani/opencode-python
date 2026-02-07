"""HTTP client utilities with proxy support."""

import os
from typing import Any

import httpx


def get_proxy_config() -> dict[str, str] | None:
    """Get proxy configuration from environment variables.
    
    Checks for standard proxy environment variables:
    - HTTPS_PROXY / https_proxy (highest priority)
    - HTTP_PROXY / http_proxy
    - ALL_PROXY / all_proxy
    
    Returns:
        Dict with proxy URLs or None if no proxy configured
    """
    proxies = {}
    
    # Check for HTTPS proxy (highest priority for HTTPS URLs)
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if https_proxy:
        proxies["https://"] = https_proxy
    
    # Check for HTTP proxy
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if http_proxy:
        proxies["http://"] = http_proxy
    
    # Check for ALL proxy (fallback)
    all_proxy = os.environ.get("ALL_PROXY") or os.environ.get("all_proxy")
    if all_proxy:
        if "https://" not in proxies:
            proxies["https://"] = all_proxy
        if "http://" not in proxies:
            proxies["http://"] = all_proxy
    
    # Check for NO_PROXY (hosts to exclude)
    no_proxy = os.environ.get("NO_PROXY") or os.environ.get("no_proxy")
    if no_proxy:
        proxies["no_proxy"] = no_proxy
    
    return proxies if proxies else None


def should_use_proxy(url: str, no_proxy: str | None) -> bool:
    """Check if URL should use proxy based on NO_PROXY setting.
    
    Args:
        url: The URL to check
        no_proxy: Comma-separated list of hosts to exclude
        
    Returns:
        True if URL should use proxy, False to bypass
    """
    if not no_proxy:
        return True
    
    # Extract hostname from URL
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
    except:
        return True
    
    # Check each no_proxy entry
    no_proxy_list = [h.strip().lower() for h in no_proxy.split(",")]
    hostname_lower = hostname.lower()
    
    for pattern in no_proxy_list:
        if not pattern:
            continue
        # Exact match
        if hostname_lower == pattern:
            return False
        # Wildcard suffix match (e.g., .local or *.local)
        if pattern.startswith("*") or pattern.startswith("."):
            suffix = pattern.lstrip("*.").lstrip(".")
            if hostname_lower.endswith(suffix):
                return False
        # Domain suffix match
        if hostname_lower.endswith("." + pattern):
            return False
    
    return True


def create_http_client(
    base_url: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """Create an HTTP client with proxy support from environment variables.
    
    Args:
        base_url: Optional base URL for all requests
        headers: Optional default headers
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to httpx.AsyncClient
        
    Returns:
        Configured httpx.AsyncClient with proxy support
    """
    client_kwargs = {
        "timeout": timeout,
        **kwargs,
    }
    
    if base_url:
        client_kwargs["base_url"] = base_url
    
    if headers:
        client_kwargs["headers"] = headers
    
    # Get proxy configuration from environment
    proxy_config = get_proxy_config()
    
    if proxy_config:
        # Remove no_proxy from proxy_config as it's handled separately
        no_proxy_hosts = proxy_config.pop("no_proxy", None)
        
        # Determine which URL to check against NO_PROXY
        url_to_check = base_url or ""
        
        if proxy_config and should_use_proxy(url_to_check, no_proxy_hosts):
            # Use the HTTPS proxy if available, otherwise HTTP proxy
            # httpx expects a single proxy URL, not a dict
            proxy_url = proxy_config.get("https://") or proxy_config.get("http://")
            if proxy_url:
                client_kwargs["proxy"] = proxy_url
    
    return httpx.AsyncClient(**client_kwargs)
