import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup, BotCommand)

# --- БЛОК КОНФИГУРАЦИИ И КОНСТАНТ ---
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
SESSION_TIMEOUT = 30  # Таймаут сессии в минутах

# --- КОНФИГУРАЦИЯ СИСТЕМЫ ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s - (%(filename)s:%(lineno)d)',
    handlers=[
        logging.FileHandler("bot_activity.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Список процедур с ценами
PROCEDURES = {
    "comp1": {"name": "Комплекс 1 (подмышки-глубокое бикини)", "price": 1550},
    "comp2": {"name": "Комплекс 2 (подмышки-глубокое бикини-голени)", "price": 2590},
    "comp3": {"name": "Комплекс 3 (подмышки-глубокое бикини-голени-бедра)", "price": 3590},
    "armpits": {"name": "Подмышечные впадины", "price": 590},
    "classic-bikini": {"name": "Бикини классическое", "price": 890},
    "deep-bikini": {"name": "Бикини глубокое", "price": 1090},
    "arms-below-elbow": {"name": "Руки ниже локтя", "price": 1190},
    "arms-above-elbow": {"name": "Руки выше локтя", "price": 1190},
    "thighs": {"name": "Бёдра", "price": 2090},
    "calves": {"name": "Голени", "price": 2090},
    "upper-lip": {"name": "Верхняя губа", "price": 420},
    "chin": {"name": "Подбородок", "price": 420},
    "cleavage": {"name": "Декольте (грудь)", "price": 540},
    "areola": {"name": "Область вокруг сосков", "price": 420},
    "stomach-line": {"name": "Линия живота", "price": 420},
    "full-stomach": {"name": "Живот (полностью)", "price": 1090},
    "lower-back": {"name": "Поясница", "price": 840},
    "full-back": {"name": "Спина (полностью)", "price": 2090},
    "fingers-and-hands": {"name": "Пальцы рук и кисти", "price": 480},
    "bet-eyebrows": {"name": "Межбровье", "price": 420},
    "cheeks": {"name": "Щёки", "price": 420},
    "neck": {"name": "Шея", "price": 420},
    "toes-and-feet": {"name": "Пальцы ног и стопы", "price": 480}
}

# Словарь для хранения текстов статичных сообщений
STATIC_MESSAGES = {
    "💰 Цены": (
            "💰 Наши цены:\n" + "\n".join([f"{v['name']} - {v['price']} руб." for v in PROCEDURES.values()]) +
            "\n\n<i>ВНИМАНИЕ! Для мужчин цена любой процедуры дороже на 20%</i>"
    ),
    "📞 Контакты": (
        "📞 Наши контакты:\n"
        "👩 Мастер: Кристина\n"
        "   VK: https://vk.com/id305430186\n"
        "   Instagram: https://www.instagram.com/mrsshnisel\n"
        "   Telegram: https://t.me/MrsEpil\n"
        "   WhatsApp: +79212659800\n"
        "🌐 Наше VK-сообщество: https://vk.com/simon_epil\n"
        "📍 Адрес: г. Выборг, ул. Приморская, д.40, кв. 14\n"
        "📱 Телефон: +79212659800\n"
        "🕒 Часы работы: 08:00-22:00 (без выходных)"
    ),
    "✅ Рекомендации": {
        "before": (
            "✅ <b>Рекомендации перед процедурой:</b>\n\n"
            "• За сутки до эпиляции сбрейте волосы бритвой НАГОЛО (лицо и ареолы сосков следует обработать депиляционным "
            "кремом).\n"
            "• Не загорать за 6-7 дней до процедуры.\n"
            "• За 3–4 недели до начала курса процедур исключить все виды депиляции (пинцет, воск, сахар, эпилятор, "
            "электроэпиляция, скребок для депиляции и пр).\n"
            "• В день процедуры не пользуйтесь дезодорантом, спиртосодержащими и косметическими средствами (масла, "
            "кремы и тд) в планируемых зонах проведения процедуры.\n"
            "• За 3–4 дня до процедуры не используйте скрабы для кожи и не пользуйтесь жёсткими щетками.\n"
            "• За 10–14 дней до процедуры не принимайте антибиотики тетрациклиновой группы, а также препараты, "
            "относящиеся к группе фторхинолонов, ретиноиды и фотосенсибилизирующие средства.\n\n"
            "<i>Соблюдение рекомендаций улучшит результат!</i>"
        ),
        "after": (
            "✅ <b>Рекомендации после процедуры:</b>\n\n"
            "• Не распаривать кожу (горячая ванна, сауна, баня) в течение 3–4 дней\n"
            "• Не использовать спиртосодержащую косметику 3–4 дня.\n"
            "• Не использовать скрабы для кожи и жёсткие щётки 4 дня\n"
            "• Не применять косметику с гликолевой кислотой и ретинолом 7 дней\n"
            "• Не загорать 14 дней\n"
            "• Не проводить депиляцию в течение всего курса процедур (воск, шугаринг, пинцет, эпилятор)\n"
            "• Наносить на обработанные зоны Бепантен или Пантенол\n"
            "• Перед выходом на улицу использовать солнцезащитные средства с SPF не менее 30\n"
            "• Провести скрабирование обработанных зон на 5–7 день\n\n"
            "<i>Соблюдение рекомендаций защитит кожу от красноты и высыпаний!</i>"
        )
    },
    "🚫 Противопоказания": (
        "⚠️ <b>АБСОЛЮТНЫЕ ПРОТИВОПОКАЗАНИЯ</b> (запрещено категорически):\n"
        "• Беременность и лактация\n"
        "• Онкологические заболевания (в т.ч. в анамнезе)\n"
        "• Эпилепсия\n"
        "• Сахарный диабет в декомпенсированной форме\n"
        "• Кожные заболевания в зоне обработки:\n"
        "  - Псориаз\n"
        "  - Экзема\n"
        "- Дерматит в активной фазе\n"
        "  - Герпес в стадии обострения\n"
        "• Фоточувствительность кожи (аллергия на свет)\n"
        "• Свежий загар (менее 2 недель)\n"
        "• Инфекционные заболевания с температурой\n\n"
        "⚖️ <b>ОТНОСИТЕЛЬНЫЕ ПРОТИВОПОКАЗАНИЯ</b> (требуют консультации врача):\n"
        "• Варикозное расширение вен (в зоне обработки)\n"
        "• Купероз (сосудистые звёздочки)\n"
        "• Родинки и пигментные пятна в зоне эпиляции\n"
        "• Приём фотосенсибилизирующих препаратов:\n"
        "  - Антибиотики (тетрациклины, фторхинолоны)\n"
        "  - Ретиноиды (в т.ч. косметика с ретинолом)\n"
        "• Недавняя депиляция воском/шугаринг (менее 3–4 недель)\n"
        "• Свежие татуировки или перманентный макияж в зоне обработки\n"
        "• Хронические заболевания в стадии обострения\n\n"
        "<i>При наличии любых противопоказаний обязательна консультация специалиста!</i>"
    ),
    "ℹ️ О салоне": (
        "🌟 <b>Несколько слов обо мне</b> 🌟\n\n"
        "Меня зовут Кристина, я мастер с 3-летним опытом, и для меня важно, чтобы Вы чувствовали себя комфортно и расслабленно.\n\n"
        "☕ <i>Маленькие удовольствия:</i>\n"
        "Пока Вы наслаждаетесь процедурой, можете выпить чашечку ароматного кофе из нашей кофемашины и угоститься конфетками\n\n"
        "💆‍♀️ <i>Профессиональное оборудование:</i>\n"
        "Аппарат Pioneer на 1200 Вт – это:\n"
        "• Максимальная эффективность\n"
        "• Бережный уход за кожей\n"
        "• Гарантированный результат\n\n"
        "✨ Ваша красота и комфорт – мой главный приоритет!\n\n"
        "Жду Вас в гости, чтобы подарить Вам не только безупречный результат, но и приятные моменты отдыха."
    )
}

# --- ИНИЦИАЛИЗАЦИЯ БОТА И ПЕРЕМЕННЫХ СЕССИИ ---
os.makedirs("logs", exist_ok=True)
bot = AsyncTeleBot(TOKEN)
user_data = {}
user_sessions = {}
# Словарь для хранения состояний, заменяет register_next_step_handler
user_states = {}


# --- ФУНКЦИИ-ПОМОЩНИКИ (Служебная логика) ---
def create_main_menu():
    """Создает клавиатуру главного меню"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("📅 Записаться на процедуру"),
        KeyboardButton("❓ Задать вопрос мастеру"),
        KeyboardButton("💰 Цены"),
        KeyboardButton("📞 Контакты"),
        KeyboardButton("✅ Рекомендации"),
        KeyboardButton("🚫 Противопоказания"),
        KeyboardButton("ℹ️ О салоне"),
    ]
    markup.add(*buttons)
    return markup


def create_cancel_menu():
    """Создает клавиатуру с одной кнопкой 'Отменить'"""
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отменить"))


async def set_bot_commands():
    """Регистрирует команды бота"""
    commands = [
        BotCommand("start", "Начать взаимодействие с ботом")
    ]
    await bot.set_my_commands(commands)


def format_booking_message(user_id, for_admin=False):
    """Создает отформатированное сообщение о записи"""
    data = user_data.get(user_id)
    if not data:
        return "Данные о записи не найдены."

    try:
        procedures_list = ", ".join(
            f"{PROCEDURES[key]['name']}"
            for key in data["procedures"]
        )
        total_price = data['total_price']
    except KeyError as e:
        logging.error(f"KeyError in format_booking_message for user {user_id}: {e}")
        return "❌ Произошла ошибка при обработке данных. Пожалуйста, начните заново."

    message = ""
    if for_admin:
        message += "📌 Новая запись!\n"
    else:
        message += "🔎 Подтвердите запись:\n"

    message += (
        f"👤 Имя: {data['name']}\n"
        f"🚻 Пол: {data['gender']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"💆 Процедуры: {procedures_list}\n"
    )

    if data.get("gender") == "Мужчина 👨":
        message += "<b>Внимание! Цена увеличена на 20% из-за пола.</b>\n"

    message += (
        f"💰 Общая стоимость: {total_price:.2f} руб.\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {data['time']}\n"
    )

    if for_admin:
        message += f"🆔 ID пользователя: {user_id}"
    else:
        message += "\nВсё верно?"

    return message


async def send_admin_notification(user_id):
    """Отправляет уведомление администратору"""
    if not ADMIN_CHAT_ID:
        logging.error("ADMIN_CHAT_ID не задан. Уведомление не отправлено.")
        return False

    try:
        if user_id not in user_data:
            logging.warning(f"Попытка отправить уведомление для несуществующего пользователя: {user_id}")
            return False

        message = format_booking_message(user_id, for_admin=True)
        if "❌ Произошла ошибка" in message:
            logging.error(f"Ошибка форматирования сообщения для пользователя {user_id}. Уведомление не отправлено.")
            return False

        await bot.send_message(ADMIN_CHAT_ID, message, parse_mode="HTML")
        logging.info(f"Уведомление отправлено администратору для пользователя {user_id}")
        return True

    except Exception as e:
        logging.error(f"Неизвестная ошибка при отправке администратору ({user_id}): {e}")
        return False


async def clean_old_sessions():
    """
    Периодически удаляет старые сессии, чтобы освободить память.
    """
    while True:
        now = datetime.now()
        expired_users = []
        for user_id, session in user_sessions.items():
            if now - session['last_activity'] > timedelta(minutes=SESSION_TIMEOUT):
                expired_users.append(user_id)

        for user_id in expired_users:
            user_sessions.pop(user_id, None)
            user_data.pop(user_id, None)
            user_states.pop(user_id, None)  # Добавлено для очистки состояния
            logging.info(f"Сессия пользователя {user_id} истекла и была удалена.")
        await asyncio.sleep(60)


# --- ОСНОВНЫЕ ОБРАБОТЧИКИ СООБЩЕНИЙ И КОЛЛБЭКОВ ---
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    """
    Обработчик команды /start
    """
    user_id = message.chat.id
    user_sessions[user_id] = {
        'active': True,
        'last_activity': datetime.now()
    }
    if user_id not in user_data:
        user_data[user_id] = {"procedures": []}

    # Очищаем состояние пользователя при старте
    user_states.pop(user_id, None)

    logging.info(f"Пользователь {user_id} начал работу с ботом.")

    await bot.send_message(
        user_id,
        "Добро пожаловать в салон лазерной эпиляции! 🏩",
        reply_markup=create_main_menu()
    )


@bot.message_handler(func=lambda msg: True)
async def update_user_activity(message):
    """Обновляет время последней активности пользователя и перенаправляет на нужный обработчик."""
    user_id = message.chat.id
    if user_id in user_sessions:
        user_sessions[user_id]['last_activity'] = datetime.now()

    if message.text == "🏠 Главное меню" or message.text == "Отменить":
        await handle_main_menu(message)
    elif message.text in STATIC_MESSAGES:
        await handle_static_messages(message)
    elif message.text == "📅 Записаться на процедуру":
        await start_booking(message)
    elif message.text == "❓ Задать вопрос мастеру":
        await start_ask_master(message)
    # Обработчики, основанные на состоянии
    elif user_states.get(user_id) == 'awaiting_name':
        await process_name_step(message)
    elif user_states.get(user_id) == 'awaiting_gender':
        await process_gender_step(message)
    elif user_states.get(user_id) == 'awaiting_phone':
        await process_phone_step(message)
    elif user_states.get(user_id) == 'awaiting_question':
        await process_ask_master(message)
    elif user_states.get(user_id) == 'awaiting_admin_reply':
        # Передаем ID пользователя, которому отвечаем
        original_user_id = user_data[user_id].get('reply_to_user_id')
        if original_user_id:
            await process_admin_reply_step(message, original_user_id)


async def handle_main_menu(message):
    """Асинхронный обработчик для кнопки "Главное меню" и "Отменить"."""
    user_id = message.chat.id
    user_data.pop(user_id, None)
    user_states.pop(user_id, None)  # Очищаем состояние
    logging.info(f"Пользователь {user_id} вернулся в главное меню.")
    await send_welcome(message)


async def handle_static_messages(message):
    """Асинхронный универсальный обработчик для статичных кнопок главного меню."""
    user_id = message.chat.id
    user_states.pop(user_id, None)  # Очищаем состояние
    text = STATIC_MESSAGES[message.text]
    logging.info(f"Пользователь {user_id} запросил: {message.text}")
    if isinstance(text, dict):
        await bot.send_message(user_id, text["before"], parse_mode="HTML")
        await bot.send_message(user_id, text["after"], parse_mode="HTML")
    else:
        await bot.send_message(user_id, text, parse_mode="HTML")


async def start_booking(message):
    """Начало процесса записи"""
    user_id = message.chat.id
    user_data[user_id] = {"procedures": []}
    user_states[user_id] = 'awaiting_name'  # Устанавливаем состояние
    logging.info(f"Пользователь {user_id} начал процесс записи.")
    await bot.send_message(
        user_id,
        "Введите ваше имя:",
        reply_markup=create_cancel_menu()
    )


# --- БЛОК ЛОГИКИ ЗАПИСИ ---
async def process_name_step(message):
    """Обработка введенного имени с проверкой допустимых символов"""
    user_id = message.chat.id

    name = message.text.strip()
    if not (2 <= len(name) <= 50):
        await bot.send_message(
            user_id,
            "❌ Имя слишком короткое или длинное (от 2 до 50 символов).\nПожалуйста, введите ваше имя еще раз:",
            reply_markup=create_cancel_menu()
        )
        return  # Не меняем состояние, ждем нового ввода

    allowed_chars = set(" -',")
    if not all(char.isalpha() or char in allowed_chars for char in name):
        await bot.send_message(
            user_id,
            "❌ Имя может содержать только буквы, пробелы и символы: - ' ,\nПримеры допустимых имен:\n- Анна-Мария\n- Иванов, Иван Иванович\n- O'Connor\n\nПожалуйста, введите ваше имя еще раз:",
            reply_markup=create_cancel_menu()
        )
        return  # Не меняем состояние

    user_data[user_id]["name"] = name
    user_states[user_id] = 'awaiting_gender'  # Меняем состояние на следующее

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Мужчина 👨"), KeyboardButton("Женщина 👩"))
    markup.add(KeyboardButton("Отменить"))

    await bot.send_message(
        user_id,
        "Пожалуйста, выберите свой пол:",
        reply_markup=markup
    )


async def process_gender_step(message):
    """Обработка выбора пола"""
    user_id = message.chat.id

    gender_choice = message.text
    if gender_choice not in ["Мужчина 👨", "Женщина 👩"]:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Мужчина 👨"), KeyboardButton("Женщина 👩"))
        markup.add(KeyboardButton("Отменить"))
        await bot.send_message(
            user_id,
            "❌ Пожалуйста, выберите один из предложенных вариантов.",
            reply_markup=markup
        )
        return  # Не меняем состояние

    user_data[user_id]["gender"] = gender_choice
    user_states[user_id] = 'awaiting_phone'  # Меняем состояние
    await bot.send_message(
        user_id,
        "Введите ваш номер телефона (11 цифр, например: 79123456789):",
        reply_markup=create_cancel_menu()
    )


async def process_phone_step(message):
    """Проверка номера телефона"""
    user_id = message.chat.id

    phone_digits = ''.join(filter(str.isdigit, message.text))
    if len(phone_digits) != 11 or phone_digits[0] not in ['7', '8']:
        await bot.send_message(
            user_id,
            "❌ Номер должен содержать 11 цифр и начинаться с 7 или 8.\nПример: 79123456789\nПопробуйте еще раз:",
            reply_markup=create_cancel_menu()
        )
        return  # Не меняем состояние

    logging.info(f"Пользователь {user_id} ввел номер телефона: {phone_digits}")

    user_data[user_id]["phone"] = f"+7{phone_digits[1:]}"
    user_states.pop(user_id, None)  # Завершаем ввод, убираем состояние
    await show_procedures_menu(user_id)


async def show_procedures_menu(chat_id):
    """Показывает меню выбора процедур"""
    user_data.setdefault(chat_id, {})
    user_data[chat_id].setdefault("procedures", [])
    user_states.pop(chat_id, None)

    markup = InlineKeyboardMarkup()
    selected_procedures = user_data[chat_id].get("procedures", [])

    # 1. Сначала добавляем каждый комплекс с новой строки
    complex_keys = ["comp1", "comp2", "comp3"]
    for key in complex_keys:
        markup.add(
            InlineKeyboardButton(
                f"{'✅' if key in selected_procedures else '◻️'} {PROCEDURES[key]['name']}",
                callback_data=f"proc_{key}"
            )
        )

    # 2. Затем добавляем все остальные процедуры по две в строку
    other_keys = [key for key in PROCEDURES if key not in complex_keys]
    for i in range(0, len(other_keys), 2):
        row_buttons = []
        key1 = other_keys[i]
        button1 = InlineKeyboardButton(
            f"{'✅' if key1 in selected_procedures else '◻️'} {PROCEDURES[key1]['name']}",
            callback_data=f"proc_{key1}"
        )
        row_buttons.append(button1)

        if i + 1 < len(other_keys):
            key2 = other_keys[i + 1]
            button2 = InlineKeyboardButton(
                f"{'✅' if key2 in selected_procedures else '◻️'} {PROCEDURES[key2]['name']}",
                callback_data=f"proc_{key2}"
            )
            row_buttons.append(button2)

        markup.row(*row_buttons)

    markup.add(InlineKeyboardButton("🔹 Завершить выбор", callback_data="procedures_done"))
    markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking"))
    await bot.send_message(chat_id, "Выберите процедуры (можно несколько)::", reply_markup=markup)


async def update_procedures_menu(message):
    """Обновляет меню выбора процедур"""
    user_id = message.chat.id
    if user_id not in user_data or "procedures" not in user_data[user_id]:
        await bot.send_message(user_id, "❌ Сессия устарела. Пожалуйста, начните заново.",
                               reply_markup=create_main_menu())
        return

    markup = InlineKeyboardMarkup()
    selected_procedures = user_data[user_id].get("procedures", [])

    # 1. Сначала добавляем каждый комплекс с новой строки
    complex_keys = ["comp1", "comp2", "comp3"]
    for key in complex_keys:
        markup.add(
            InlineKeyboardButton(
                f"{'✅' if key in selected_procedures else '◻️'} {PROCEDURES[key]['name']}",
                callback_data=f"proc_{key}"
            )
        )

    # 2. Затем добавляем все остальные процедуры по две в строку
    other_keys = [key for key in PROCEDURES if key not in complex_keys]
    for i in range(0, len(other_keys), 2):
        row_buttons = []
        key1 = other_keys[i]
        button1 = InlineKeyboardButton(
            f"{'✅' if key1 in selected_procedures else '◻️'} {PROCEDURES[key1]['name']}",
            callback_data=f"proc_{key1}"
        )
        row_buttons.append(button1)

        if i + 1 < len(other_keys):
            key2 = other_keys[i + 1]
            button2 = InlineKeyboardButton(
                f"{'✅' if key2 in selected_procedures else '◻️'} {PROCEDURES[key2]['name']}",
                callback_data=f"proc_{key2}"
            )
            row_buttons.append(button2)

        markup.row(*row_buttons)

    markup.add(InlineKeyboardButton("🔹 Завершить выбор", callback_data="procedures_done"))
    markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking"))

    try:
        await bot.edit_message_text(chat_id=user_id, message_id=message.message_id,
                                    text="Выберите процедуры (можно несколько):", reply_markup=markup)
    except Exception as e:
        logging.warning(f"Ошибка при обновлении меню для пользователя {user_id}: {e}")


# Обработчик для inline кнопок. Он должен быть асинхронным.
@bot.callback_query_handler(func=lambda call: call.data.startswith("proc_"))
async def toggle_procedure_selection(call):
    """Обработка выбора/отмены процедуры"""
    user_id = call.message.chat.id
    await bot.answer_callback_query(call.id)

    if user_id not in user_data:
        await bot.send_message(user_id, "❌ Сессия устарела. Начните заново.", reply_markup=create_main_menu())
        return

    procedure_key = call.data.split("_")[1]
    procedures = user_data[user_id].setdefault("procedures", [])
    if procedure_key in procedures:
        procedures.remove(procedure_key)
        logging.info(f"Пользователь {user_id} убрал процедуру {procedure_key}.")
    else:
        procedures.append(procedure_key)
        logging.info(f"Пользователь {user_id} добавил процедуру {procedure_key}.")

    await update_procedures_menu(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "procedures_done")
async def finish_procedures_selection(call):
    """Завершение выбора процедур"""
    user_id = call.message.chat.id
    await bot.answer_callback_query(call.id)
    try:
        if user_id not in user_data:
            await bot.send_message(user_id, "❌ Сессия устарела. Начните заново.", reply_markup=create_main_menu())
            return

        procedures = user_data[user_id].setdefault("procedures", [])
        if not procedures:
            await bot.send_message(user_id, "❌ Выберите хотя бы одну процедуру!")
            return

        valid_procedures = [key for key in procedures if key in PROCEDURES]
        if not valid_procedures:
            await bot.send_message(user_id, "❌ Выберите хотя бы одну процедуру!")
            return

        user_data[user_id]["procedures"] = valid_procedures
        total_price = sum(PROCEDURES[key]["price"] for key in valid_procedures)
        if user_data[user_id].get("gender") == "Мужчина 👨":
            total_price *= 1.2

        user_data[user_id]["total_price"] = total_price
        await show_date_selection(call.message)
    except KeyError as e:
        logging.error(f"Ошибка KeyError при завершении выбора процедур для пользователя {user_id}: {e}")
        await bot.send_message(user_id, "❌ Произошла ошибка. Пожалуйста, начните заново.",
                               reply_markup=create_main_menu())
    except Exception as e:
        logging.error(f"Неизвестная ошибка при завершении выбора процедур для пользователя {user_id}: {e}")
        await bot.send_message(user_id, "❌ Произошла ошибка. Попробуйте снова.", reply_markup=create_main_menu())


async def show_date_selection(message):
    """Показывает выбор даты"""
    user_id = message.chat.id
    if user_id not in user_data:
        await bot.send_message(user_id, "❌ Сессия устарела. Пожалуйста, начните заново.",
                               reply_markup=create_main_menu())
        return

    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(1, 31)]
    # Возвращаем row_width к значению по умолчанию (1)
    markup = InlineKeyboardMarkup(row_width=3)  # Меняем row_width для дат
    markup.add(*[InlineKeyboardButton(date, callback_data=f"date_{date}") for date in dates])
    markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking"))
    try:
        await bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text="Выберите дату:",
                                    reply_markup=markup)
    except Exception as e:
        logging.warning(f"Ошибка при переходе к выбору даты для пользователя {user_id}: {e}")
        await bot.send_message(user_id, "Выберите дату:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("date_"))
async def select_appointment_date(call):
    """Обработка выбора даты"""
    user_id = call.message.chat.id
    await bot.answer_callback_query(call.id)
    if user_id not in user_data:
        await bot.send_message(user_id, "❌ Сессия устарела. Начните заново.", reply_markup=create_main_menu())
        return
    user_data[user_id]["date"] = call.data.split("_")[1]
    await show_time_selection(call.message)


async def show_time_selection(message):
    """Показывает выбор времени"""
    user_id = message.chat.id
    if user_id not in user_data:
        await bot.send_message(user_id, "❌ Сессия устарела. Пожалуйста, начните заново.",
                               reply_markup=create_main_menu())
        return

    times = [f"{hour}:{minute:02d}" for hour in range(8, 22) for minute in (0, 30)]

    markup = InlineKeyboardMarkup(row_width=4)  # Устанавливаем row_width = 4
    buttons = [InlineKeyboardButton(time, callback_data=f"time_{time}") for time in times]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking"))

    try:
        await bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text="Выберите время:",
                                    reply_markup=markup)
    except Exception as e:
        logging.warning(f"Ошибка при переходе к выбору времени для пользователя {user_id}: {e}")
        await bot.send_message(user_id, "Выберите время:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
async def select_appointment_time(call):
    """Обработка выбора времени"""
    user_id = call.message.chat.id
    await bot.answer_callback_query(call.id)
    if user_id not in user_data:
        await bot.send_message(user_id, "❌ Сессия устарела. Начните заново.", reply_markup=create_main_menu())
        return
    user_data[user_id]["time"] = call.data.split("_")[1]
    await show_confirmation(call.message)


async def show_confirmation(message):
    """Показывает подтверждение записи"""
    user_id = message.chat.id
    if user_id not in user_data or "procedures" not in user_data[user_id]:
        await bot.send_message(user_id, "❌ Сессия устарела. Пожалуйста, начните заново.",
                               reply_markup=create_main_menu())
        return

    confirmation_text = format_booking_message(user_id)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Подтвердить запись", callback_data="confirm_booking"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking"),
    )

    try:
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=message.message_id,
            text=confirmation_text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.warning(f"Ошибка при подтверждении записи для пользователя {user_id}: {e}")
        await bot.send_message(user_id, confirmation_text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "confirm_booking")
async def confirm_appointment(call):
    """Подтверждение записи."""
    user_id = call.message.chat.id
    await bot.answer_callback_query(call.id)
    if user_id not in user_data:
        await bot.send_message(user_id, "❌ Сессия устарела. Начните заново.", reply_markup=create_main_menu())
        return

    final_message_text = (
            f"✅ Запись оформлена!\n\nДетали:\n"
            f"👤 Имя: {user_data[user_id]['name']}\n"
            f"🚻 Пол: {user_data[user_id]['gender']}\n"
            f"📞 Телефон: {user_data[user_id]['phone']}\n"
            f"💆 Процедуры: " + ", ".join([f"{PROCEDURES[key]['name']}"
                                          for key in user_data[user_id]["procedures"]]) + "\n" +
            (f"<b>Внимание! Цена увеличена на 20% из-за пола.</b>\n" if user_data[user_id].get(
                "gender") == "Мужчина 👨" else "") +
            f"💰 Общая стоимость: {user_data[user_id]['total_price']:.2f} руб.\n"
            f"📅 Дата: {user_data[user_id]['date']}\n"
            f"⏰ Время: {user_data[user_id]['time']}\n\n"
            f"Ожидайте звонка от администратора для подтверждения записи и уточнения деталей!\n\n"
            f"Вы можете начать новую запись или выбрать опцию в меню ниже."
    )

    try:
        await bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        await bot.send_message(
            chat_id=user_id,
            text=final_message_text,
            reply_markup=create_main_menu(),
            parse_mode="HTML"
        )
        await send_admin_notification(user_id)
        user_data.pop(user_id, None)
        user_states.pop(user_id, None)
        logging.info(f"Запись для пользователя {user_id} завершена и данные удалены.")
    except Exception as e:
        logging.error(f"Ошибка при подтверждении записи для пользователя {user_id}: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "cancel_booking")
async def cancel_appointment(call):
    """Отмена записи"""
    user_id = call.message.chat.id
    await bot.answer_callback_query(call.id)
    await bot.send_message(user_id, "❌ Запись отменена.", reply_markup=create_main_menu())
    user_data.pop(user_id, None)
    user_states.pop(user_id, None)
    logging.info(f"Запись для пользователя {user_id} отменена.")


# --- ЛОГИКА ДЛЯ ВОПРОСОВ МАСТЕРУ ---
@bot.message_handler(func=lambda msg: msg.text == "❓ Задать вопрос мастеру")
async def start_ask_master(message):
    """Начало диалога с мастером"""
    user_id = message.chat.id
    if not ADMIN_CHAT_ID:
        await bot.send_message(user_id, "❌ В данный момент мастер недоступен. Пожалуйста, попробуйте позже.",
                               reply_markup=create_main_menu())
        logging.error("ADMIN_CHAT_ID не задан. Невозможно начать диалог с мастером.")
        return

    user_states[user_id] = 'awaiting_question'
    await bot.send_message(
        user_id,
        "✏️ Напишите ваш вопрос мастеру.",
        reply_markup=create_cancel_menu()
    )


async def process_ask_master(message):
    """Отправляет вопрос администратору с кнопкой для ответа"""
    user_id = message.chat.id

    if not message.text:
        await bot.send_message(user_id, "❌ Сообщение не может быть пустым. Пожалуйста, напишите ваш вопрос:",
                               reply_markup=create_cancel_menu())
        return

    try:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("💬 Ответить", callback_data=f"reply_to_{user_id}"),
            InlineKeyboardButton("🚫 Проигнорировать", callback_data=f"ignore_{user_id}")
        )

        await bot.send_message(
            ADMIN_CHAT_ID,
            f"👤 **Новый вопрос от пользователя:**\n\n{message.text}\n\n"
            f"ID пользователя: `{user_id}`",
            parse_mode="Markdown",
            reply_markup=markup
        )
        await bot.send_message(user_id, "✅ Ваш вопрос отправлен мастеру. Ожидайте ответа.",
                               reply_markup=create_main_menu())
        user_states.pop(user_id, None)  # Завершаем состояние
        logging.info(f"Вопрос от пользователя {user_id} отправлен администратору с кнопкой ответа.")

    except Exception as e:
        logging.error(f"Ошибка при отправке вопроса от {user_id} администратору: {e}")
        await bot.send_message(user_id, "❌ Не удалось отправить вопрос. Пожалуйста, попробуйте позже.",
                               reply_markup=create_cancel_menu())


@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_to_"))
async def handle_admin_reply_button(call):
    """Обработка нажатия на кнопку 'Ответить пользователю'"""
    admin_id = call.message.chat.id
    original_user_id = int(call.data.split("_")[2])

    user_states[admin_id] = 'awaiting_admin_reply'  # Устанавливаем состояние для администратора
    user_data[admin_id] = {'reply_to_user_id': original_user_id}  # Сохраняем ID пользователя для ответа

    await bot.edit_message_text(chat_id=admin_id, message_id=call.message.message_id,
                                text=f"Напишите ваш ответ для пользователя с ID `{original_user_id}`.\n\n"
                                     f"Нажмите 'Отменить', чтобы прервать.", parse_mode="Markdown")
    await bot.send_message(
        admin_id,
        "✏️ Введите ваш ответ:",
        reply_markup=create_cancel_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("ignore_"))
async def handle_admin_ignore_button(call):
    """Обработка нажатия на кнопку 'Проигнорировать'"""
    admin_id = call.message.chat.id
    original_user_id = int(call.data.split("_")[1])

    await bot.delete_message(chat_id=admin_id, message_id=call.message.message_id)
    await bot.send_message(
        admin_id,
        f"🚫 Вопрос от пользователя с ID `{original_user_id}` был проигнорирован.",
        reply_markup=create_main_menu(),
        parse_mode="Markdown"
    )
    logging.info(f"Администратор {admin_id} проигнорировал вопрос от пользователя {original_user_id}.")


async def process_admin_reply_step(message, original_user_id):
    """Обрабатывает введенный администратором ответ и отправляет его пользователю"""
    admin_id = message.chat.id

    try:
        reply_text = message.text
        if not reply_text:
            await bot.send_message(admin_id, "❌ Ответ не может быть пустым. Пожалуйста, введите текст ответа:",
                                   reply_markup=create_cancel_menu())
            return

        # Отправляем ответ пользователю
        await bot.send_message(
            original_user_id,
            "💬 Ответ от мастера:\n\n" + reply_text,
            reply_markup=create_main_menu()
        )
        await bot.send_message(
            admin_id,
            f"✅ Ответ успешно отправлен пользователю с ID `{original_user_id}`.",
            reply_markup=create_main_menu(),
            parse_mode="Markdown"
        )
        user_states.pop(admin_id, None)  # Завершаем состояние администратора
        logging.info(f"Администратор {admin_id} отправил ответ пользователю {original_user_id}.")

    except Exception as e:
        logging.error(f"Неизвестная ошибка при отправке ответа от {admin_id} к {original_user_id}: {e}")
        await bot.send_message(admin_id, "❌ Произошла непредвиденная ошибка.", reply_markup=create_main_menu())


async def start_bot():
    """Асинхронно запускает бота и фоновую задачу для очистки сессий"""
    await set_bot_commands()
    await asyncio.gather(
        bot.infinity_polling(skip_pending=True),
        clean_old_sessions()
    )


if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logging.info("Бот выключается...")
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)
