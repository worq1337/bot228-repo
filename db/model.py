from sqlalchemy import Integer, BigInteger, String, Text, Index, Boolean, DateTime
from sqlalchemy.orm import mapped_column
from datetime import datetime
from .base import Base


class Spyusers(Base):
    __tablename__ = "spyusers"

    id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id = mapped_column(BigInteger, nullable=False, index=True)
    ref_id = mapped_column(BigInteger)
    bot_name = mapped_column(String(255))

    # Add table arguments with index
    __table_args__ = (
        Index('idx_spyusers_user_id', 'user_id'),
    )


class MessageCache(Base):
    """Table for storing cached messages."""
    __tablename__ = "message_cache"

    message_id = mapped_column(BigInteger, primary_key=True)  # Changed from Integer to BigInteger
    chat_id = mapped_column(BigInteger, nullable=False)
    user_full_name = mapped_column(String(255), nullable=False)
    text = mapped_column(Text, nullable=False)
    message_type = mapped_column(String(50), nullable=False, default="text")
    additional_info = mapped_column(Text, nullable=True)
    user_id = mapped_column(BigInteger, nullable=False)


class Webhook(Base):
    __tablename__ = "webhooks"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id = mapped_column(BigInteger, nullable=False)  # ✅ Должно быть
    bot_username = mapped_column(String(255), nullable=False)  # ✅ Должно быть
    token = mapped_column(String(255), nullable=False)  # ✅ Должно быть
    webhook_url = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index('idx_webhook_url', 'webhook_url'),
    )

