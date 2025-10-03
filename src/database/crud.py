from sqlalchemy.orm import Session
from . import models
from datetime import datetime, date, timedelta
from typing import List, Optional

def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, username: str = None, 
                first_name: str = None, last_name: str = None) -> models.User:
    db_user = models.User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    db_stats = models.UserStats(user_id=db_user.id)
    db.add(db_stats)
    db.commit()
    
    return db_user

def create_habit(db: Session, user_id: int, name: str, category: str, 
                frequency_type: str = "daily", frequency_value: List = None,
                reminder_time: str = None, difficulty: str = "medium") -> models.Habit:
    habit = models.Habit(
        user_id=user_id,
        name=name,
        category=category,
        frequency_type=frequency_type,
        frequency_value=frequency_value or [],
        reminder_time=reminder_time,
        difficulty=difficulty
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    
    stats = db.query(models.UserStats).filter(models.UserStats.user_id == user_id).first()
    if stats:
        stats.total_habits_created += 1
        stats.current_active_habits += 1
        db.commit()
    
    return habit

def get_user_habits(db: Session, user_id: int, active_only: bool = True) -> List[models.Habit]:
    query = db.query(models.Habit).filter(models.Habit.user_id == user_id)
    if active_only:
        query = query.filter(models.Habit.is_active == True)
    return query.order_by(models.Habit.created_at.desc()).all()

def mark_habit_completed(db: Session, habit_id: int, user_id: int, 
                        notes: str = None, mood: str = None) -> models.HabitCompletion:
    completion = models.HabitCompletion(
        habit_id=habit_id,
        user_id=user_id,
        notes=notes,
        mood=mood
    )
    db.add(completion)
    
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit:
        habit.current_streak += 1
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
    
    stats = db.query(models.UserStats).filter(models.UserStats.user_id == user_id).first()
    if stats:
        stats.total_completions += 1
    
    db.commit()
    db.refresh(completion)
    return completion
