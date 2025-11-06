from sqlalchemy import Column, String, BigInteger, DateTime, func, CheckConstraint, ForeignKey, Integer
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone_no = Column(String(10), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)     
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship(
        "Profiles",  
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy='joined'
    )

    booking = relationship(
        "Bookings",
        back_populates="user",
        lazy='joined'
    )
    
    room_status_history = relationship(
        "RoomStatusHistory",
        back_populates="user",  
        lazy='joined'
    )
    
    role = relationship("Roles", back_populates="user", uselist=False)

    __table_args__ = (
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="check_valid_email_format"
        ),
        CheckConstraint("char_length(first_name) <= 50", name="check_first_name_length"),
        CheckConstraint("char_length(last_name) <= 50", name="check_last_name_length"),
        CheckConstraint(
            "phone_no ~ '^[1-9][0-9]{9}$'",
            name="check_valid_phone_number"
        ),
    )
