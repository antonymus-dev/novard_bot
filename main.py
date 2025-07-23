import asyncio
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

TOKEN = "7982478031:AAHDwNmUIBZp_0LKrlS6cyu6BBdgpAtKc6k"
ADMIN_ID = 1642890158

def back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="go_back")
    return builder.as_markup()

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# --- Состояния ---
class CourseStates(StatesGroup):
    choosing_module = State()
    in_module = State()
    writing_feedback = State()

# --- База данных ---


def add_user(chat_id):
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT chat_id FROM users")
    return [row[0] for row in cursor.fetchall()]

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        user_id INTEGER PRIMARY KEY,
        m0 INTEGER DEFAULT 0,
        m1 INTEGER DEFAULT 0,
        m2 INTEGER DEFAULT 0,
        m3 INTEGER DEFAULT 0
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        user_id INTEGER,
        username TEXT,
        feedback TEXT,
        submitted_at TEXT
    )
""")
conn.commit()

# Таблица для подписчиков
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY
    )
""")
conn.commit()

# --- Модули курса ---
MODULES = [
    {"title": "Вебинар 1: Введение", "video": "https://example.com/webinar1", "material_link": "https://drive.google.com/drive/folders/10Vsq0-CDwda_7zrC1z5A4Z6bH3PkmBoi?usp=sharing"},
    {"title": "Вебинар 2: Промптинг", "video": "https://example.com/webinar2", "material_link": "https://drive.google.com/drive/folders/1j6zPFHcr82FRkgzUbrO8OdhjCXSSd0fn?usp=sharing"},
    {"title": "Вебинар 3: Визуализация", "video": "https://example.com/webinar3", "material_link": "https://drive.google.com/drive/folders/1yOqabtMHYH_GrgjJtnS1n_k6oS8myee-?usp=sharing"},
    {"title": "Вебинар 4: Автоматизация", "video": "https://example.com/webinar4", "material_link": "https://drive.google.com/drive/folders/140iQi5wHLp0GAIlOuTsI2OsSMa6YRR0A?usp=sharing"},
    {"title": "Вебинар 5: Продвинутые техники", "video": "https://example.com/webinar5", "material_link": "https://drive.google.com/drive/folders/1c_TSVegOYMnuaFSpb50xm26EOTvXi69R?usp=sharing"},
]

# --- Кнопки ---
def start_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать", callback_data="start_course_menu")
    kb.adjust(1)
    return kb.as_markup()

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔹 Пройти курс", callback_data="start_course")
    kb.button(text="🔹 Записи и материалы", callback_data="materials")
    kb.button(text="🔹 Задать вопрос", callback_data="ask_question")
    kb.button(text="🔹 Помощь / FAQ", callback_data="faq")
    kb.button(text="🔹 Мой прогресс", callback_data="my_progress")
    kb.button(text="🔹 Получить сертификат", callback_data="certificate")
    kb.button(text="🔹 Обратная связь", callback_data="feedback")
    kb.adjust(2)
    return kb.as_markup()

def modules_keyboard(prefix="module"):
    kb = InlineKeyboardBuilder()
    for i, m in enumerate(MODULES):
        kb.button(text=m["title"], callback_data=f"{prefix}_{i}")
    kb.adjust(1)
    kb.button(text="⬅️ Назад", callback_data="go_back")
    kb.adjust(1)
    return kb.as_markup()

def module_actions_keyboard(index: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="📤 Отправить домашнее задание", callback_data=f"submit_hw_{index}")
    kb.button(text="✅ Пройден!", callback_data=f"complete_{index}")
    kb.button(text="⬅️ Назад", callback_data="go_back")
    return kb.as_markup()

# --- Хендлеры ---
@dp.message(F.text.lower() == "/start")
async def welcome_message(message: Message):
    add_user(message.chat.id)
    cursor.execute("INSERT OR IGNORE INTO progress (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()

    photo = FSInputFile("files/welcome.jpg")  # путь к твоему изображению

    await message.answer_photo(
        photo=photo,
        caption=(
            "👋 Добро пожаловать в обучающий бот по нейросетям!\n\n"
            "Здесь вы сможете:\n"
            "- Смотреть записи вебинаров и материалы\n"
            "- Выполнять домашние задания и отслеживать прогресс\n"
            "- Получить сертификат после прохождения курса\n\n"
            "Нажмите кнопку *Начать*, чтобы перейти в меню."
        ),
        reply_markup=start_button(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "start_course")
async def start_course(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите вебинар:", reply_markup=modules_keyboard())
    await state.set_state(CourseStates.choosing_module)

@dp.callback_query(F.data.startswith("module_"))
async def open_module(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    module = MODULES[index]
    #await callback.message.answer(
    #    f"📚 Вы выбрали: {module['title']}\n🎥 Видеозапись: {module['video']}"
    #)
    #file = FSInputFile(module["file"])
    #await callback.message.answer_document(file, caption="📄 Домашнее задание")
    #await callback.message.answer("⬇️ Выберите действие:", reply_markup=module_actions_keyboard(index))
    #await state.set_state(CourseStates.in_module)
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await callback.message.answer("Скоро здесь появится видеозапись вебинара.", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("submit_hw_"))
async def submit_homework(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await callback.message.answer("Пожалуйста, отправьте домашнее задание...", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("complete_"))
async def complete_module(callback: CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[1])
    cursor.execute(f"UPDATE progress SET m{index} = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await callback.message.answer("✅ Модуль отмечен как пройден!", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "my_progress")
async def show_progress(callback: CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT m0, m1, m2, m3, m4 FROM progress WHERE user_id = ?", (user_id,))
    result = cursor.fetchone() or (0, 0, 0, 0, 0)
    progress = "\n".join(
        f"{'✅' if done else '❌'} {MODULES[i]['title']}" for i, done in enumerate(result)
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await callback.message.answer(f"🇺🇳 Ваш прогресс:\n{progress}", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "materials")
async def materials(callback: CallbackQuery):
    await callback.message.edit_text("Выберите модуль:", reply_markup=modules_keyboard(prefix="docs"))

@dp.callback_query(F.data.startswith("docs_"))
async def docs_module(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])

    # Проверяем, есть ли ссылка на материалы
    material_link = MODULES[index].get("material_link")

    if material_link:
        await callback.message.answer(
            f"📂 *Материалы для {MODULES[index]['title']}*\n"
            f"[Открыть материалы]({material_link})",
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer("Материалы для этого вебинара пока недоступны.")

    # Добавляем кнопку Назад
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    kb.adjust(1)
    await callback.message.answer("Вернуться в главное меню:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "ask_question")
async def ask_question(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Общий чат", url="https://t.me/+Bgj6eTVC5QwxOTRi")
    kb.button(text="👤 Личное сообщение", url="https://t.me/vorobidze")
    kb.button(text="⬅️ Назад", callback_data="go_back")
    kb.adjust(1)
    await callback.message.answer("Выберите способ связи:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "faq")
async def faq(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await callback.message.answer(
        """❓ *Помощь и ответы на вопросы*

Этот бот создан для прохождения онлайн-курса по нейросетям. Вот как им пользоваться шаг за шагом:

---

*1. Главное меню*
После запуска бота командой */start* вы увидите главное меню с кнопками:
- **Пройти курс** — доступ к вебинарам и домашним заданиям.
- **Записи и материалы** — файлы и презентации для каждого вебинара.
- **Задать вопрос** — ссылки на общий чат и личные контакты преподавателя.
- **Помощь / FAQ** — текущая инструкция.
- **Мой прогресс** — проверка, какие модули уже пройдены.
- **Получить сертификат** — выдаётся после завершения всех модулей.
- **Обратная связь** — оставить отзыв о курсе.

---

*2. Как пройти курс*
- Нажмите кнопку **"Пройти курс"**.
- Выберите нужный вебинар из списка.
- Ознакомьтесь с видеозаписью и материалами.
- После просмотра выполните домашнее задание:
  - Нажмите кнопку **"Отправить домашнее задание"**;
  - Пришлите текстовое сообщение или файл с выполненным заданием.
- Когда задание выполнено, отметьте модуль как **"Пройден"**.

---

*3. Материалы*
- В разделе **"Записи и материалы"** находятся все файлы для вебинаров (презентации, методички).
- Выберите нужный модуль, чтобы скачать материалы.

---

*4. Прогресс*
- В разделе **"Мой прогресс"** вы видите список всех модулей:
  - Зеленая галочка (✅) — модуль пройден.
  - Красный крестик (❌) — модуль ещё не пройден.
- Прогресс обновляется автоматически, когда вы отмечаете модуль как пройден.

---

*5. Сертификат*
- Сертификат выдается после прохождения *всех* модулей.
- Нажмите кнопку **"Получить сертификат"** — бот проверит прогресс и выдаст инструкцию по получению сертификата.

---

*6. Как задать вопрос*
- Кнопка **"Задать вопрос"** откроет варианты связи:
  - Общий чат участников курса.
  - Личный контакт преподавателя.

---

*7. Как оставить отзыв*
- Кнопка **"Обратная связь"** позволит написать отзыв:
  - После нажатия введите ваш отзыв одним сообщением.
  - Отзыв будет передан преподавателю.

---

*8. Кнопка Назад*
- В каждом разделе есть кнопка **"⬅️ Назад"**, чтобы быстро вернуться в главное меню.

---

Если что-то не работает или остались вопросы — напишите в чат поддержки: [ссылка на чат] или свяжитесь напрямую с преподавателем: [ссылка на контакт].
""",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "certificate")
async def certificate(callback: CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT m0, m1, m2, m3 FROM progress WHERE user_id = ?", (user_id,))
    modules = cursor.fetchone() or (0, 0, 0, 0)
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    if all(modules):
        await callback.message.answer(
            "📜 Поздравляем! Вы прошли курс. Мы отправим сертификат на вашу почту.",
            reply_markup=kb.as_markup()
        )
    else:
        left = "\n".join(f"{MODULES[i]['title']}" for i, m in enumerate(modules) if not m)
        await callback.message.answer(
            f"❗ Чтобы получить сертификат, нужно пройти все модули.\nОсталось:\n{left}",
            reply_markup=kb.as_markup()
        )

@dp.callback_query(F.data == "feedback")
async def feedback(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await callback.message.answer("✍️ Напишите свой отзыв — одним сообщением.", reply_markup=kb.as_markup())
    await state.set_state(CourseStates.writing_feedback)

@dp.message(CourseStates.writing_feedback)
async def save_feedback(message: Message, state: FSMContext):
    cursor.execute("INSERT INTO feedback (user_id, username, feedback, submitted_at) VALUES (?, ?, ?, ?)",
                   (message.from_user.id, message.from_user.username or "", message.text, datetime.now().isoformat()))
    conn.commit()
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await bot.send_message(ADMIN_ID, f"📩 Новый отзыв от @{message.from_user.username}:\n{message.text}")
    await message.answer("Спасибо за ваш отзыв! ❤️", reply_markup=kb.as_markup())
    await state.clear()

# ================== АДМИН-ПАНЕЛЬ ==================

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    # Создаем клавиатуру с обязательным параметром `keyboard`
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Сделать рассылку")],
            [KeyboardButton(text="👥 Список подписчиков")],
            [KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True
    )

    await message.answer("Панель администратора:", reply_markup=kb)

# Список подписчиков
@dp.message(F.text == "👥 Список подписчиков")
async def list_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = get_all_users()
    text = f"Подписчиков: {len(users)}\n" + "\n".join(map(str, users[:50]))
    if len(users) > 50:
        text += "\n..."
    await message.answer(text)

# Статистика
@dp.message(F.text == "📊 Статистика")
async def stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = len(get_all_users())
    await message.answer(f"Всего подписчиков: {count}")

# Рассылка
class BroadcastStates(StatesGroup):
    waiting_text = State()

@dp.message(F.text == "📢 Сделать рассылку")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Отправь текст рассылки:")
    await state.set_state(BroadcastStates.waiting_text)

@dp.message(BroadcastStates.waiting_text)
async def broadcast_send(message: Message, state: FSMContext):
    text = message.text
    users = get_all_users()
    sent = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            await asyncio.sleep(0.05)
            sent += 1
        except:
            pass
    await message.answer(f"Рассылка завершена. Отправлено {sent} сообщений.")
    await state.clear()

@dp.callback_query(F.data == "start_course_menu")
async def open_main_menu(callback: CallbackQuery):
    await callback.message.edit_text("Выберите действие:", reply_markup=main_menu())

@dp.callback_query(F.data == "go_back")
async def go_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите действие:", reply_markup=main_menu())
    
    

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())