# Proxy Support Implementation Summary

## Overview
Added proxy support to OpenCode Python CLI using standard environment variables.

## Environment Variables Supported

- `HTTPS_PROXY` / `https_proxy` - HTTPS proxy URL (highest priority)
- `HTTP_PROXY` / `http_proxy` - HTTP proxy URL
- `ALL_PROXY` / `all_proxy` - Fallback proxy for both HTTP and HTTPS
- `NO_PROXY` / `no_proxy` - Comma-separated list of hosts to bypass proxy

## Usage Examples

### Basic Proxy Setup
```bash
export HTTPS_PROXY=http://proxy.company.com:8080
python -m opencode.cli run "hi"
```

### With Authentication
```bash
export HTTPS_PROXY=http://username:password@proxy.company.com:8080
python -m opencode.cli run "hi"
```

### Bypass Proxy for Local Hosts
```bash
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1,.local,192.168.0.0/24
python -m opencode.cli run "hi"
```

### Different Proxies for HTTP/HTTPS
```bash
export HTTP_PROXY=http://http-proxy.example.com:3128
export HTTPS_PROXY=http://https-proxy.example.com:8080
python -m opencode.cli run "hi"
```

## Implementation Details

### Files Modified

1. **`opencode/util/http.py`** (NEW)
   - `get_proxy_config()` - Reads proxy settings from environment
   - `should_use_proxy()` - Checks NO_PROXY exclusions
   - `create_http_client()` - Creates httpx client with proxy support

2. **`opencode/provider/provider.py`**
   - Updated `OpenCodeProvider` to use proxy configuration
   - Automatically detects and applies proxy settings
   - Respects NO_PROXY for local endpoints

3. **`opencode/tool/websearch.py`**
   - Updated to use proxy-aware HTTP client

4. **`opencode/tool/webfetch.py`**
   - Updated to use proxy-aware HTTP client

5. **`opencode/tool/codesearch.py`**
   - Updated to use proxy-aware HTTP client

## Features

✅ Automatic proxy detection from environment variables  
✅ Support for HTTP and HTTPS proxies  
✅ NO_PROXY support with pattern matching  
✅ Works with authentication (user:pass@proxy)  
✅ Falls back from HTTPS_PROXY to HTTP_PROXY to ALL_PROXY  
✅ Local endpoints (localhost, 127.0.0.1) automatically bypassed when in NO_PROXY  
✅ Domain suffix matching (e.g., `.local` matches `api.local`)  

## Testing

Test scenarios that pass:
1. ✅ HTTPS_PROXY with external URL
2. ✅ NO_PROXY exclusion for localhost
3. ✅ HTTP_PROXY fallback
4. ✅ Proxy bypass for .local domains

## Example Output

```
[OpenCodeProvider] Using endpoint: https://opencode.ai/zen/v1
[OpenCodeProvider] Using proxy: http://proxy.company.com:8080
Session: ses_xxx...
```

Or when bypassing proxy:
```
[OpenCodeProvider] Using endpoint: http://localhost:11434
[OpenCodeProvider] Local mode detected
[OpenCodeProvider] Proxy configured but http://localhost:11434 is in NO_PROXY
```
