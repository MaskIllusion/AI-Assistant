import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from database.database import get_db
from database import crud

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

class HabitTrackerBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        if not self.token:
            raise ValueError("BOT_TOKEN не найден в переменных окружения")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("habits", self.list_habits))
        self.application.add_handler(CommandHandler("add_habit", self.add_habit))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        
        # Обработчики сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        db = next(get_db())
        
        # Проверяем есть ли пользователь в базе
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user:
            # Создаем нового пользователя
            db_user = crud.create_user(
                db, 
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            welcome_message = f"""
 Добро пожаловать, {user.first_name}!

Я - твой умный помощник для трекинга привычек!
С моей помощью ты сможешь:
  Создавать и отслеживать привычки
  Получать напоминания
  Видеть свой прогресс
  Получать персональные советы от AI

Начнем с создания твоей первой привычки!
Нажми /add_habit чтобы добавить привычку.
"""
        else:
            welcome_message = f"""
 С возвращением, {user.first_name}!

Рад снова тебя видеть! Готов продолжать работу над привычками?

Доступные команды:
/add_habit - Добавить новую привычку
/habits - Посмотреть мои привычки
/stats - Моя статистика
/help - Помощь
"""

        keyboard = [
            [KeyboardButton("/add_habit"), KeyboardButton("/habits")],
            [KeyboardButton("/stats"), KeyboardButton("/help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
 **Помощь по командам:**

**Основные команды:**
/start - Начать работу с ботом
/add_habit - Добавить новую привычку
/habits - Посмотреть мои привычки
/stats - Моя статистика и прогресс

**Управление привычками:**
После добавления привычки ты будешь получать напоминания.
Отмечай выполнение привычек через кнопки в уведомлениях.

**AI советы:**
Бот будет анализировать твой прогресс и предлагать персональные рекомендации!

Начни с команды /add_habit чтобы создать первую привычку! 
"""
        await update.message.reply_text(help_text)

    async def add_habit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /add_habit"""
        user = update.effective_user
        db = next(get_db())
        
        # Проверяем что пользователь существует
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("Сначала запусти бота командой /start")
            return
        
        # Сохраняем состояние - пользователь добавляет привычку
        context.user_data['adding_habit'] = True
        context.user_data['habit_stage'] = 'name'
        
        await update.message.reply_text(
            "Отлично! Давай создадим новую привычку.\n\n"
            " **Шаг 1 из 4:** Как называется твоя привычка?\n"
            "Например: 'Утренняя зарядка', 'Чтение книги', 'Прогулка'"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        message_text = update.message.text
        db = next(get_db())
        
        # Проверяем состояние добавления привычки
        if context.user_data.get('adding_habit'):
            await self.handle_habit_creation(update, context, message_text, db, user.id)
            return
        
        await update.message.reply_text(
            "Не понял твоего сообщения \n"
            "Используй команды из меню или /help для справки."
        )

    async def handle_habit_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  message_text: str, db, user_id: int):
        """Обработка процесса создания привычки"""
        stage = context.user_data.get('habit_stage')
        
        if stage == 'name':
            # Сохраняем название и переходим к категории
            context.user_data['habit_name'] = message_text
            context.user_data['habit_stage'] = 'category'
            
            categories_keyboard = [
                [" Здоровье", " Продуктивность"],
                [" Обучение", " Психология"],
                [" Спорт", " Образ жизни"]
            ]
            reply_markup = ReplyKeyboardMarkup(categories_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f" **Шаг 2 из 4:** Отличное название '{message_text}'!\n\n"
                " Теперь выбери категорию:",
                reply_markup=reply_markup
            )
            
        elif stage == 'category':
            # Сохраняем категорию и переходим к частоте
            context.user_data['habit_category'] = message_text.replace("", "").strip()
            context.user_data['habit_stage'] = 'frequency'
            
            frequency_keyboard = [
                [" Ежедневно", " По дням недели"],
                [" Через день", " Конкретные дни"]
            ]
            reply_markup = ReplyKeyboardMarkup(frequency_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f" **Шаг 3 из 4:** Категория '{message_text}' выбрана!\n\n"
                " Как часто ты планируешь выполнять эту привычку?",
                reply_markup=reply_markup
            )
            
        elif stage == 'frequency':
            # Сохраняем частоту и завершаем создание
            context.user_data['habit_frequency'] = message_text
            context.user_data['habit_stage'] = 'complete'
            
            # Создаем привычку в базе данных
            habit = crud.create_habit(
                db=db,
                user_id=user_id,
                name=context.user_data['habit_name'],
                category=context.user_data['habit_category'],
                frequency_type="daily",  # Упрощенная версия
                reminder_time="09:00"
            )
            
            # Очищаем состояние
            context.user_data.clear()
            
            # Возвращаем обычную клавиатуру
            keyboard = [
                [KeyboardButton("/add_habit"), KeyboardButton("/habits")],
                [KeyboardButton("/stats"), KeyboardButton("/help")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f" **Поздравляю! Привычка создана!**\n\n"
                f" **Название:** {habit.name}\n"
                f" **Категория:** {habit.category}\n"
                f" **Частота:** Ежедневно\n\n"
                f"Теперь я буду напоминать тебе о выполнении этой привычки!\n"
                f"Используй /habits чтобы посмотреть все свои привычки.",
                reply_markup=reply_markup
            )

    async def list_habits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список привычек пользователя"""
        user = update.effective_user
        db = next(get_db())
        
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("Сначала запусти бота командой /start")
            return
        
        habits = crud.get_user_habits(db, db_user.id)
        
        if not habits:
            await update.message.reply_text(
                "У тебя пока нет привычек \n"
                "Добавь первую привычку командой /add_habit"
            )
            return
        
        habits_text = " **Твои привычки:**\n\n"
        for i, habit in enumerate(habits, 1):
            status = " Активна" if habit.is_active else " На паузе"
            habits_text += f"{i}. **{habit.name}**\n"
            habits_text += f"    {habit.category} |  Серия: {habit.current_streak} дней\n"
            habits_text += f"   {status}\n\n"
        
        await update.message.reply_text(habits_text)

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику пользователя"""
        user = update.effective_user
        db = next(get_db())
        
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user:
            await update.message.reply_text("Сначала запусти бота командой /start")
            return
        
        stats = crud.get_user_stats(db, db_user.id)
        habits = crud.get_user_habits(db, db_user.id)
        
        stats_text = f" **Статистика {user.first_name}**\n\n"
        stats_text += f" **Всего привычек:** {stats.total_habits_created}\n"
        stats_text += f" **Активных привычек:** {stats.current_active_habits}\n"
        stats_text += f" **Всего выполнено:** {stats.total_completions} раз\n"
        stats_text += f" **Текущая серия:** {stats.total_streak_days} дней\n\n"
        
        if habits:
            completion_rate = (stats.total_completions / (len(habits) * stats.total_streak_days)) * 100 if stats.total_streak_days > 0 else 0
            stats_text += f" **Процент выполнения:** {completion_rate:.1f}%\n"
        
        stats_text += "\nПродолжай в том же духе! "
        
        await update.message.reply_text(stats_text)

    def run(self):
        """Запуск бота"""
        print(" Бот запускается...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = HabitTrackerBot()
    bot.run()
