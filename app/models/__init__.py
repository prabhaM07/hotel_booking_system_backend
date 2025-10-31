# app/models/__init__.py
from app.core.database_postgres import Base

# ============================================
# ENUMS (import first)
# ============================================
from app.models.Enum import BookingStatusEnum, PaymentStatusEnum, RoomStatusEnum

# ============================================
# ASSOCIATION TABLES (import BEFORE models that use them)
# ============================================
from app.models.associations import room_type_feature
from app.models.associations import role_scope

# ============================================
# INDEPENDENT TABLES (no foreign keys)
# ============================================
from app.models.role import Role
from app.models.scope import Scopes
from app.models.bed_type import BedType
from app.models.features import Feature
from app.models.floor import Floor
from app.models.addon import Addon

# ============================================
# RoomTypeWithSize must come AFTER room_type_feature
# ============================================
from app.models.room_type import RoomTypeWithSize

# ============================================
# User must come before Profile and Bookings
# ============================================
from app.models.user import User

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
# PaymentStatus depends on Bookings - MOVED AFTER Bookings
# ============================================
from app.models.payment_status_history import PaymentStatusHistory

# ============================================
# BookingStatusHistory depends on Bookings
# ============================================
from app.models.booking_status_history import BookingStatusHistory

# ============================================
# Profile depends on User
# ============================================
from app.models.user_profile import Profile

# ============================================
# Junction tables and other dependent models
# ============================================
from app.models.roomType_bedType import RoomTypeBedType
from app.models.booking_addon import BookingAddon
from app.models.reschedule import Reschedule

__all__ = [
    "Base",
    # Enums
    "BookingStatusEnum",
    "PaymentStatusEnum", 
    "RoomStatusEnum",
    # Association tables
    "room_type_feature",
    # Independent models
    "Role",
    "Scopes",
    "BedType",
    "Feature",
    "Floor",
    "Addon",
    # Core models in dependency order
    "RoomTypeWithSize",
    "User",
    "Rooms",
    "Bookings",
    "PaymentStatus",
    "BookingStatusHistory",
    "PaymentStatusHistory",
    "RoomStatusHistory", 
    "Profile",
    # Junction tables
    "RoomTypeBedType",
    "BookingAddon",
    "Reschedule",

]