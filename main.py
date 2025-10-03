#!/usr/bin/env python3
"""
Главный файл запуска Habit Tracker Bot
"""
from src.bot.main import HabitTrackerBot

if __name__ == "__main__":
    print(" Запуск Умного помощника для трекинга привычек...")
    bot = HabitTrackerBot()
    bot.run()
