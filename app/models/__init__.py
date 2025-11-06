# app/models/__init__.py
from app.core.database_postgres import Base

# ============================================
# ENUMS (import first)
# ============================================
from app.models.Enum import BookingStatusEnum, PaymentStatusEnum, RoomStatusEnum

# ============================================
# ASSOCIATION TABLES (import BEFORE models that use them)
# ============================================
from app.models.associations import room_type_features
from app.models.associations import role_scopes

# ============================================
# INDEPENDENT TABLES (no foreign keys)
# ============================================
from app.models.role import Roles
from app.models.scope import Scopes
from app.models.bed_type import BedTypes
from app.models.features import Features
from app.models.floor import Floors
from app.models.addon import Addons

# ============================================
# RoomTypeWithSize must come AFTER room_type_feature
# ============================================
from app.models.room_type import RoomTypeWithSizes

# ============================================
# User must come before Profile and Bookings
# ============================================
from app.models.user import Users

# ============================================
# Rooms depends on RoomTypeWithSize and Floor
# ============================================
from app.models.rooms import Rooms


# ============================================
# RoomStatusHistory depends on Rooms and RoomTypeWithSize
# ============================================
from app.models.room_status_history import RoomStatusHistory


# ============================================
# Bookings depends on User and Rooms
# ============================================
from app.models.bookings import Bookings

# ============================================
# Bookings depends on User and Rooms
# ============================================
from app.models.payment import Payments

from app.models.rating_reviews import RatingsReviews

from app.models.refund import Refunds
# ============================================
# PaymentStatus depends on Bookings - MOVED AFTER Bookings
# ============================================

from app.models.payment_status_history import PaymentStatusHistory

# ============================================
# BookingStatusHistory depends on Bookings
# ============================================
from app.models.booking_status_history import BookingStatusHistory


from app.models.refund_status_history import RefundStatusHistory

# ============================================
# Profile depends on User
# ============================================
from app.models.user_profile import Profiles

# ============================================
# Junction tables and other dependent models
# ============================================
from app.models.roomType_bedType import RoomTypeBedTypes
from app.models.booking_addon import BookingAddons
from app.models.reschedule import Reschedules

__all__ = [
    "Base",
    # Enums
    "BookingStatusEnum",
    "PaymentStatusEnum", 
    "RoomStatusEnum",
    # Association tables
    "room_type_features",
    "role_scopes",
    # Independent models
    "Roles",
    "Scopes",
    "BedTypes",
    "Features",
    "Floors",
    "Addons",
    # Core models in dependency order
    "RoomTypeWithSizes",
    "Users",
    "Rooms",
    "Bookings",
    "Payments",
    "RatingsReviews",
    "Refunds",
    "PaymentStatus",
    "BookingStatusHistory",
    "PaymentStatusHistory",
    "RoomStatusHistory",
    "RefundStatusHistory",
    "Profiles",
    # Junction tables
    "RoomTypeBedTypes",
    "BookingAddons",
    "Reschedules",

]