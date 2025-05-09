import re

async def is_bot_token(token: str) -> bool:
    """Validate that a string is a properly formatted bot token"""
    return bool(re.match(r'^\d+:[\w-]+$', token))
