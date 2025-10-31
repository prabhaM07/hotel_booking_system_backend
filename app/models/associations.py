# app/models/associations.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship

# Many-to-many association tables
room_type_feature = Table(
    'room_type_feature',
    Base.metadata,
    Column('room_type_id', Integer, ForeignKey('room_type_with_size.id',ondelete="CASCADE"), primary_key=True),
    Column('feature_id', Integer, ForeignKey('feature.id',ondelete="CASCADE"), primary_key=True)
    
)

role_scope = Table(
    'role_scope',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('role.id',ondelete="CASCADE"), primary_key=True),
    Column('scope_id', Integer, ForeignKey('scope.id',ondelete="CASCADE"), primary_key=True)
)