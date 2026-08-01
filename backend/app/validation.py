BOT_DESCRIPTION_MAX_LENGTH = 280


def normalize_bot_description(value: str) -> str:
    """Return a trimmed bot description or raise a user-facing validation error."""
    description = value.strip()
    if not description:
        raise ValueError("Bot description is required")
    if len(description) > BOT_DESCRIPTION_MAX_LENGTH:
        raise ValueError(f"Bot description must be {BOT_DESCRIPTION_MAX_LENGTH} characters or fewer")
    return description
