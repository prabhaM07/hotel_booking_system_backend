# app/models/associations.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.core.database_postgres import Base
from sqlalchemy.orm import relationship

# Many-to-many association tables
room_type_features = Table(
    'room_type_features',
    Base.metadata,
    Column('room_type_id', Integer, ForeignKey('room_type_with_sizes.id',ondelete="CASCADE"), primary_key=True),
    Column('feature_id', Integer, ForeignKey('features.id',ondelete="CASCADE"), primary_key=True)
    
)

role_scopes = Table(
    'role_scopes',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id',ondelete="CASCADE"), primary_key=True),
    Column('scope_id', Integer, ForeignKey('scopes.id',ondelete="CASCADE"), primary_key=True)
)