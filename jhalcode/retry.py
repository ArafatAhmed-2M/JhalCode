"""Retry policy mirroring OpenCode/Claude Code: retry 429/5xx/network, never auth/bad-request."""
import random
import time

MAX_RETRIES = 5

RETRYABLE_MARKS = ("429", "500", "502", "503", "504", "rate limit", "overloaded",
                   "server error", "server_error", "try again", "timeout", "timed out",
                   "connection", "temporarily", "unavailable")
FATAL_MARKS = ("401", "402", "403", "404", "context_length_exceeded", "context overflow",
               "insufficient_quota", "invalid_api_key", "invalid key", "not supported",
               "no endpoints found", "no payment method", "usage_not_included")


def retryable(err: str) -> bool:
    s = err.lower()
    if any(k in s for k in FATAL_MARKS):
        return False
    return any(k in s for k in RETRYABLE_MARKS)


def wait(attempt: int, headers=None) -> float:
    try:
        if headers:
            for k in ("retry-after", "retry-after-ms"):
                if k in headers:
                    v = float(headers[k])
                    return min(v / 1000 if "ms" in k else v, 120)
    except Exception:
        pass
    return min(2 * (2 ** attempt) + random.uniform(0, 1), 30)


def run(label: str, fn, notify=None):
    last = RuntimeError("request failed")
    for n in range(MAX_RETRIES + 1):
        try:
            return fn()
        except Exception as e:
            last = e
            if n >= MAX_RETRIES or not retryable(str(e)):
                raise
            w = wait(n, getattr(e, "headers", None))
            if notify:
                notify(f"retry {n + 1}/{MAX_RETRIES} ({label}) in {w:.0f}s...")
            time.sleep(w)
    raise last
