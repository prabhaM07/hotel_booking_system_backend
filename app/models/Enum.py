import enum

class BookingStatusEnum(str, enum.Enum):
    """Enum for booking status values"""
    PENDING = "pending" # Booking request received but not yet confirmed
    CONFIRMED = "confirmed" # Booking successfully reserved and confirmed
    CANCELLED = "cancelled" # Booking was cancelled by guest or admin
    COMPLETED = "completed" # Booking has ended successfully
    

class PaymentStatusEnum(str, enum.Enum):
    """Enum for payment status values"""
    PENDING = "pending" # Payment started but not yet completed
    PAID = "paid" # Payment successfully received
    REFUNDED = "refunded" # Payment returned to guest
    FAILED = "failed" # Payment attempt failed


class RoomStatusEnum(str, enum.Enum):
    """Enum for room status values"""
    AVAILABLE = "available"       # Room is clean, unoccupied, and ready for booking
    OCCUPIED = "occupied"         # Guest is currently staying in the room
    RESERVED = "reserved"         # Room is booked for a future date
    MAINTENANCE = "maintenance"   # Room is under repair and not bookable

