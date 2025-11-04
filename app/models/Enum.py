import enum

class BookingStatusEnum(str, enum.Enum):
    """Enum for booking status values"""
    PENDING = "pending" # Booking request received but not yet confirmed
    CONFIRMED = "confirmed" # Booking successfully reserved and confirmed
    CANCELLED = "cancelled" # Booking was cancelled by guest or admin
    COMPLETED = "completed" # Booking has ended successfully
    

class PaymentStatusEnum(str, enum.Enum):
    """Enum for payment status values"""
    PAID = "paid" # Payment successfully received
    REFUNDED = "refunded" # Payment returned to guest
    FAILED = "failed" # Payment attempt failed


class RoomStatusEnum(str, enum.Enum):
    """Enum for room status values"""
    AVAILABLE = "available"       # Room is clean, unoccupied, and ready for booking
    MAINTENANCE = "maintenance"   # Room is under repair and not bookable


class RefundStatusEnum(str, enum.Enum):
    """Enum for refund status values"""
    APPROVED = "approved"             # Refund request approved by admin
    REJECTED = "rejected"             # Refund request denied
    COMPLETED = "completed"           # Refund has been successfully completed
