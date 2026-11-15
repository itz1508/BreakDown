"""Token bucket implementation."""


class TokenBucket:
    """Rate limiter."""

    def refill(self) -> None:
        """Refill tokens."""
