import logging
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Настройка логирования только для пользовательских действий
logger = logging.getLogger('user_actions')
logger.setLevel(logging.INFO)

# Создаем handler для файла
file_handler = logging.FileHandler('user_actions.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - USER ACTION - %(message)s'))

# Создаем handler для консоли (опционально)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - USER ACTION - %(message)s'))

# Добавляем handlers к нашему логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Отключаем propagation для нашего логгера
logger.propagate = False

# Данные из файла
historical_events = [
    "30 ноября 1939 – 12 марта 1940 г.г. советско-финская война.",
    "декабрь 1939 г. исключение СССР из Лиги Наций.",
    "22 июня 1941 г. нападение Германии на СССР, начало Великой Отечественной войны.",
    "23 июня 1941 г. образовала Ставка Главного командования (Ставка Верховного Главнокомандования).",
    "30 июня 1941 г. образовал ГКО (Государственный комитет обороны).",
    "10 июля – 10 сентября 1941 г. бои за Смоленск.",
    "8 сентября 1941 г. начало блокады Ленинграда.",
    "30 сентября 1941 – апрель 1942 г.г. бои за Москву.",
    "19 октября 1941 г. объявление осадного положения в Москве.",
    "7 ноября 1941 г. парад на Красной площади в Москве.",
    "5-6 декабря 1941 г. начало контрактушения Красной Армии под Москвой.",
    "декабрь 1941 г. нападение войск Японии на Перл-Харбор, вступление США в войну.",
    "28 июля 1942 г. приказ № 227 «Ни шагу назад!».",
    "июль – декабрь 1942 г. битва за Кавказ.",
    "17 июля 1942 – 2 февраля 1943 г.г. Сталинградская битва.",
    "январь 1943 г. прорыв блокады Ленинграда.",
    "ноябрь – декабрь 1943 г. Тегеранская конференция.",
    "5 июля – 23 августа 1943 г. Курская битва.",
    "12 июля 1943 г. танковое сражение под Прохоровкой.",
    "5 августа 1943 г. освобождение Орла и Белгорода, 1-й салют в Москве.",
    "25 августа – 23 декабря 1943 г. битва за Днепр: освобождение Киева, Левобережной и части Правобережной Украины.",
    "6 ноября 1943 г. освобождение Киева.",
    "27 января 1944 г. полностью снята блокада Ленинграда.",
    "май 1944 г. освобождение Крыма, взятие Севастополя.",
    "6 июня 1944 г. открытие союзниками 2-го фронта.",
    "июль – август 1944 г. освобождение Белоруссии (операция «Багратион»).",
    "август – октябрь 1944 г. освобождение Молдавии.",
    "сентябрь – октябрь 1944 г. освобождение Прибаттики.",
    "июнь 1944 – май 1945 г.г. освобождение стран Восточной Европы.",
    "4 – 11 февраля 1945 г. Ялтинская конференция.",
    "16 апреля – 2 мая 1945 г. битва за Берлин.",
    "8 мая 1945 г. подписание акта о безоговорочной капитуляции.",
    "9 мая 1945 г. освобождение Праги (Пражская операция).",
    "9 мая 1945 г. окончание Великой Отечественной войны.",
    "17 июля – 2 августа 1945 г. Потсдамская конференция.",
    "6, 9 августа 1945 г. бомбардировка Хиросимы и Нагасаки.",
    "8 августа 1945 г. вступление СССР в войну против Японии.",
    "2 сентября 1945 г. подписание акта о безоговорочной капитуляции Японии, окончание II Мировой войны.",
    "1945 г. создание ООН.",
    "1946 – 1953 г.г. волна идеологических и политических репрессий (постановления о журналах, кинофильмах, музыкальных произведениях, борьба с космополитизмом, «лешниградское дело», «дело врачей»); апогей сталинизма.",
    "март 1946 г. СНК преобразовал в Совет Министров.",
    "1947 г. денежная реформа, отмена карточной системы.",
    "1949 г. образование НАТО.",
    "1949 г. создание СЭВ.",
    "1949 г. испытание 1-й советской атомной бомбы.",
    "октябрь 1952 г. ВКП(б) переименовала в КПСС.",
    "5 марта 1953 г. смерть Сталина."
]

# Состояния для ConversationHandler
LEARNING, TESTING = range(2)

# Клавиатура для главного меню
main_keyboard = ReplyKeyboardMarkup([
    ['📚 Обучающий режим', '📝 Тестовый режим'],
    ['❌ Выйти из режима']
], resize_keyboard=True)


# Функция для логирования действий пользователя
def log_user_action(user_id, username, action):
    logger.info(f"UserID: {user_id}, Username: {username}, Action: {action}")


# Функция для извлечения даты из события
def extract_date(event):
    words = event.split()
    for word in words:
        if any(char.isdigit() for char in word) and any(char.isalpha() for char in word):
            return word
        if any(char.isdigit() for char in word) and '-' in word:
            return word
        if any(char.isdigit() for char in word) and '.' in word:
            return word
    for word in words:
        if len(word) == 4 and word.isdigit():
            return word
    return "Не удалось извлечь дату"


# Команда старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_action(user.id, user.username, "started the bot")

    await update.message.reply_text(
        "Привет! Я бот для зачета по истории.\n"
        "Пиваршев шизоид \n"
        "Выберите режим работы:",
        reply_markup=main_keyboard
    )


# Обучающий режим
async def learning_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_action(user.id, user.username, "entered learning mode")

    context.user_data['mode'] = 'learning'
    context.user_data['used_events'] = []

    available_events = [e for e in historical_events if e not in context.user_data['used_events']]
    if not available_events:
        context.user_data['used_events'] = []
        available_events = historical_events.copy()
        log_user_action(user.id, user.username, "reset learning events")

    event = random.choice(available_events)
    context.user_data['used_events'].append(event)
    context.user_data['current_event'] = event

    log_user_action(user.id, user.username, f"shown event: {event[:50]}...")
    await update.message.reply_text(f"📚 Обучающий режим:\n\n{event}\n\nНажмите любую кнопку для продолжения...")
    return LEARNING


# Тестовый режим
async def test_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_action(user.id, user.username, "entered test mode")

    context.user_data['mode'] = 'test'
    context.user_data['used_events'] = []

    available_events = [e for e in historical_events if e not in context.user_data['used_events']]
    if not available_events:
        context.user_data['used_events'] = []
        available_events = historical_events.copy()
        log_user_action(user.id, user.username, "reset test events")

    event = random.choice(available_events)
    context.user_data['used_events'].append(event)
    context.user_data['current_event'] = event

    correct_date = extract_date(event)
    context.user_data['correct_date'] = correct_date

    event_without_date = event.replace(correct_date, '_____')
    log_user_action(user.id, user.username, f"test question: {event[:50]}...")
    await update.message.reply_text(f"📝 Тестовый режим:\n\n{event_without_date}\n\nВведите дату:")
    return TESTING


# Обработка ответов в обучающем режиме
async def handle_learning_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_action(user.id, user.username, "pressed next in learning mode")

    if len(context.user_data['used_events']) >= len(historical_events):
        await update.message.reply_text("Все события изучены! Начнем заново.")
        context.user_data['used_events'] = []
        log_user_action(user.id, user.username, "all events learned, resetting")

    available_events = [e for e in historical_events if e not in context.user_data['used_events']]
    if not available_events:
        context.user_data['used_events'] = []
        available_events = historical_events.copy()

    event = random.choice(available_events)
    context.user_data['used_events'].append(event)
    context.user_data['current_event'] = event

    log_user_action(user.id, user.username, f"next event: {event[:50]}...")
    await update.message.reply_text(f"📚 Следующее событие:\n\n{event}\n\nНажмите любую кнопку для продолжения...")
    return LEARNING


# Обработка ответов в тестовом режиме
async def handle_test_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_answer = update.message.text.strip()
    correct_date = context.user_data['correct_date']

    log_user_action(user.id, user.username, f"test answer: '{user_answer}' for correct: '{correct_date}'")

    if user_answer.lower() in correct_date.lower() or correct_date.lower() in user_answer.lower():
        await update.message.reply_text("✅ Правильно! 👍")
        log_user_action(user.id, user.username, "correct answer")
    else:
        await update.message.reply_text(f"❌ Неправильно. Правильный ответ: {correct_date}")
        log_user_action(user.id, user.username, "wrong answer")

    # Переходим к следующему вопросу
    if len(context.user_data['used_events']) >= len(historical_events):
        await update.message.reply_text("Тест завершен! Все события пройдены.")
        log_user_action(user.id, user.username, "test completed all events")
        return ConversationHandler.END

    available_events = [e for e in historical_events if e not in context.user_data['used_events']]
    if not available_events:
        await update.message.reply_text("Тест завершен! Все события пройдены.")
        log_user_action(user.id, user.username, "test completed all events")
        return ConversationHandler.END

    event = random.choice(available_events)
    context.user_data['used_events'].append(event)
    context.user_data['current_event'] = event

    correct_date = extract_date(event)
    context.user_data['correct_date'] = correct_date

    event_without_date = event.replace(correct_date, '_____')
    log_user_action(user.id, user.username, f"next test question: {event[:50]}...")
    await update.message.reply_text(f"📝 Следующий вопрос:\n\n{event_without_date}\n\nВведите дату:")
    return TESTING


# Выход из режима
async def exit_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mode = context.user_data.get('mode', 'unknown')
    log_user_action(user.id, user.username, f"exited {mode} mode")

    await update.message.reply_text(
        "Режим завершен. Выберите новый режим:",
        reply_markup=main_keyboard
    )
    return ConversationHandler.END


# Основная функция
def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    application = Application.builder().token('8330291150:AAHYo_kOkYDrawBvpnSmGVUtQqdaYH6-NWM').build()

    # Обработчики команд
    application.add_handler(CommandHandler('start', start))

    # ConversationHandler для обучающего режима
    learning_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📚 Обучающий режим$'), learning_mode)],
        states={
            LEARNING: [MessageHandler(filters.TEXT & ~filters.Regex('^❌ Выйти из режима$'), handle_learning_response)]
        },
        fallbacks=[MessageHandler(filters.Regex('^❌ Выйти из режима$'), exit_mode)]
    )

    # ConversationHandler для тестового режима
    test_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📝 Тестовый режим$'), test_mode)],
        states={
            TESTING: [MessageHandler(filters.TEXT & ~filters.Regex('^❌ Выйти из режима$'), handle_test_response)]
        },
        fallbacks=[MessageHandler(filters.Regex('^❌ Выйти из режима$'), exit_mode)]
    )

    application.add_handler(learning_conv_handler)
    application.add_handler(test_conv_handler)

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()