"""Session context compaction and management."""

from dataclasses import dataclass
from typing import Any

from opencode.util import create as create_logger

log = create_logger({"service": "session.compaction"})


# Minimum tokens to prune
PRUNE_MINIMUM = 20_000
# Protect recent tokens from pruning
PRUNE_PROTECT = 40_000


@dataclass
class ContextStats:
    """Statistics about context usage."""
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cache_read: int
    cache_write: int
    is_overflow: bool


def estimate_tokens(text: str) -> int:
    """Estimate token count from text.
    
    Rough approximation: ~4 characters per token for English text.
    """
    return len(text) // 4


def check_overflow(
    messages: list[dict[str, Any]],
    max_context: int = 200000,
    max_output: int = 128000
) -> ContextStats:
    """Check if context window is overflowing.
    
    Args:
        messages: List of message dictionaries
        max_context: Maximum context size in tokens
        max_output: Maximum output size in tokens
        
    Returns:
        ContextStats with overflow information
    """
    total_input = 0
    total_output = 0
    
    for msg in messages:
        content = msg.get("content", "")
        role = msg.get("role", "")
        
        tokens = estimate_tokens(content)
        
        if role == "assistant":
            total_output += tokens
        else:
            total_input += tokens
    
    total = total_input + total_output
    usable = max_context - max_output
    is_overflow = total > usable
    
    return ContextStats(
        total_tokens=total,
        input_tokens=total_input,
        output_tokens=total_output,
        cache_read=0,
        cache_write=0,
        is_overflow=is_overflow
    )


def prune_messages(
    messages: list[dict[str, Any]],
    protect_recent: int = PRUNE_PROTECT
) -> list[dict[str, Any]]:
    """Prune old messages to reduce context size.
    
    Strategy:
    1. Keep system message (always first)
    2. Keep most recent messages up to PRUNE_PROTECT tokens
    3. Remove or compact older messages
    
    Args:
        messages: List of messages
        protect_recent: Number of recent tokens to protect
        
    Returns:
        Pruned message list
    """
    if not messages:
        return messages
    
    # Always keep system message (first message if role is "system")
    result = []
    if messages[0].get("role") == "system":
        result.append(messages[0])
        messages = messages[1:]
    
    # Calculate tokens from the end backwards
    total_tokens = 0
    cutoff_index = len(messages)
    
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        tokens = estimate_tokens(msg.get("content", ""))
        total_tokens += tokens
        
        if total_tokens >= protect_recent:
            cutoff_index = i
            break
    
    # Keep messages from cutoff onwards (most recent)
    result.extend(messages[cutoff_index:])
    
    pruned_count = cutoff_index
    if pruned_count > 0:
        log.info(f"Pruned {pruned_count} old messages", {"protected": len(result) - (1 if result and result[0].get("role") == "system" else 0)})
    
    return result


def compact_messages(
    messages: list[dict[str, Any]],
    summary: str | None = None
) -> list[dict[str, Any]]:
    """Compact messages by replacing old ones with a summary.
    
    Args:
        messages: List of messages
        summary: Optional pre-generated summary
        
    Returns:
        Compacted message list with summary
    """
    if not messages:
        return messages
    
    # Keep system message and last few messages
    result = []
    if messages[0].get("role") == "system":
        result.append(messages[0])
    
    # Generate or use provided summary
    if summary is None:
        # Count messages being compacted
        old_messages = messages[1:-3] if len(messages) > 4 else []
        if old_messages:
            summary = f"[Previous conversation: {len(old_messages)} messages summarized]"
        else:
            summary = "[Previous conversation summarized]"
    
    # Add summary as a system message
    result.append({
        "role": "system",
        "content": f"Context summary: {summary}"
    })
    
    # Keep last 3 messages for context
    result.extend(messages[-3:])
    
    log.info("Compacted messages", {"original": len(messages), "result": len(result)})
    
    return result


def middle_out_prune(
    messages: list[dict[str, Any]],
    keep_start: int = 2,
    keep_end: int = 4,
    max_tokens: int = 160000
) -> list[dict[str, Any]]:
    """Prune messages using "middle-out" strategy.
    
    This keeps the beginning (system prompt, initial context) and 
    the end (recent messages) but removes the middle part.
    
    Args:
        messages: List of messages
        keep_start: Number of messages to keep from start
        keep_end: Number of messages to keep from end
        max_tokens: Maximum tokens allowed
        
    Returns:
        Messages with middle section removed
    """
    if len(messages) <= keep_start + keep_end:
        return messages
    
    # Check if we're under the limit
    total_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
    if total_tokens <= max_tokens:
        return messages
    
    # Keep start and end, remove middle
    start = messages[:keep_start]
    end = messages[-keep_end:]
    
    # Add a placeholder for removed content
    middle_placeholder = {
        "role": "system",
        "content": f"[... {len(messages) - keep_start - keep_end} messages removed to fit context window ...]"
    }
    
    result = start + [middle_placeholder] + end
    
    log.info("Middle-out pruning applied", {
        "original": len(messages),
        "removed": len(messages) - keep_start - keep_end,
        "result": len(result)
    })
    
    return result


class ContextManager:
    """Manages conversation context to stay within token limits."""
    
    def __init__(
        self,
        max_context: int = 200000,
        max_output: int = 128000,
        strategy: str = "auto"
    ):
        self.max_context = max_context
        self.max_output = max_output
        self.strategy = strategy
    
    def optimize(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Optimize messages to fit in context window.
        
        Args:
            messages: List of messages
            
        Returns:
            Optimized message list
        """
        if not messages:
            return messages
        
        # Check current usage
        stats = check_overflow(messages, self.max_context, self.max_output)
        
        if not stats.is_overflow:
            return messages
        
        log.info("Context overflow detected", {
            "total": stats.total_tokens,
            "max": self.max_context - self.max_output
        })
        
        # Apply strategy
        if self.strategy == "prune":
            return prune_messages(messages)
        elif self.strategy == "compact":
            return compact_messages(messages)
        elif self.strategy == "middle-out":
            return middle_out_prune(messages)
        else:  # auto
            # Try middle-out first, then pruning
            result = middle_out_prune(messages)
            stats = check_overflow(result, self.max_context, self.max_output)
            if stats.is_overflow:
                result = prune_messages(result)
            return result


def get_context_manager(
    max_context: int = 200000,
    strategy: str = "auto"
) -> ContextManager:
    """Get a context manager instance.
    
    Args:
        max_context: Maximum context size
        strategy: Optimization strategy (auto, prune, compact, middle-out)
        
    Returns:
        ContextManager instance
    """
    return ContextManager(
        max_context=max_context,
        strategy=strategy
    )
