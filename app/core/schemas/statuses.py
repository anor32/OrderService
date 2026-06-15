from enum import StrEnum


class OutboxStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"


class InboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"


class OrderStatus(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
