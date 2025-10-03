from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language_code = Column(String(10), default="ru")
    timezone = Column(String(50), default="Europe/Moscow")
    
    notification_time = Column(String(5), default="09:00")
    motivation_level = Column(String(20), default="medium")
    goals = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    habits = relationship("Habit", back_populates="user")
    habit_completions = relationship("HabitCompletion", back_populates="user")

class Habit(Base):
    __tablename__ = "habits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), default="medium")
    
    frequency_type = Column(String(20), default="daily")
    frequency_value = Column(JSON, default=list)
    reminder_time = Column(String(5))
    
    target_streak = Column(Integer, default=21)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="habits")
    completions = relationship("HabitCompletion", back_populates="habit")

class HabitCompletion(Base):
    __tablename__ = "habit_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    completion_date = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    notes = Column(Text)
    mood = Column(String(20))
    difficulty_level = Column(String(20))
    
    habit = relationship("Habit", back_populates="completions")
    user = relationship("User", back_populates="habit_completions")

class UserStats(Base):
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    total_habits_created = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)
    current_active_habits = Column(Integer, default=0)
    
    completion_rate = Column(Integer, default=0)
    total_streak_days = Column(Integer, default=0)
    
    best_completion_time = Column(String(5))
    most_productive_day = Column(String(10))
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    recommendation_type = Column(String(50))
    content = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")
    
    is_applied = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
