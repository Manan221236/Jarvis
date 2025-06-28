from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from smart_scheduler.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # For now, we'll just have a default user
    # Later we'll add proper authentication
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
