import logging
import requests
import sqlite3
import json
from datetime import datetime, timedelta
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup,
                       WebAppInfo, ReplyKeyboardMarkup, KeyboardButton)
from telegram.ext import (Application, CommandHandler, MessageHandler, filters,
                           ContextTypes, CallbackQueryHandler)

TELEGRAM_TOKEN = "8761327056:AAG23S-7rlmkXmvXDdVQwjEJ0_EAdIfRmPM"
GEMINI_API_KEY = "AIzaSyDH-jXkG9rML7TjRkFXlDxt6Fsjv0KCAr0"
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# ── Exely API (заполнить когда получишь ключ) ──────────────────
EXELY_API_KEY  = ""          # ← вставь сюда ключ
EXELY_HOTEL_ID = ""          # ← вставь ID отеля
EXELY_ENABLED  = False       # ← поставь True после добавления ключа

MINI_APP_URL   = "https://accki-nagibator.github.io/medinatown-bot/booking.html"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
#  ПЕРЕВОДЫ
# ══════════════════════════════════════════════════════════════
T = {
    "ru": {
        "welcome": (
            "✨ Добро пожаловать в *Medinatown Hotel*, {name}!\n\n"
            "Я ваш персональный AI‑консьерж, доступен 24/7.\n\n"
            "Чем могу помочь?"
        ),
        "btn_book":    "📅 Бронировать",
        "btn_info":    "ℹ️ Об отеле",
        "btn_avail":   "🔍 Номера",
        "btn_manager": "📞 Менеджер",
        "btn_review":  "⭐ Отзыв",
        "btn_lang":    "🌐 Язык",
        "info_text": (
            "🏨 *Medinatown Hotel*\n\n"
            "📍 ул. Мукими 58А, Ташкент\n"
            "📞 +998 (55) 515-07-07\n"
            "✉️ medinatownhotel@gmail.com\n"
            "🌐 medinatown.uz\n\n"
            "🛏 *Номера (всего 30):*\n"
            "• Делюкс King — 12 номеров, 24 м²\n"
            "• Делюкс Twin — 15 номеров, 18–24 м²\n"
            "• Люкс King   —  3 номера,  34 м²\n\n"
            "✅ *Удобства:* Кондиционер • Халат • WiFi\n"
            "Smart TV • Сейф • Фен • Мини-бар • Завтрак\n\n"
            "🍽 *Ресторан* — круглосуточно, 60 мест\n"
            "🌇 *Терраса MINA* (5 эт.) — 11:00–05:00\n"
            "🍹 *Лобби-бар*\n\n"
            "🚗 4 км от аэропорта • 5 км от вокзала\n"
            "🚇 Метро Новза — 2 км\n\n"
            "💳 VISA / MasterCard\n"
            "🎁 Скидка 10% при бронировании с сайта"
        ),
        "avail_title":  "🔍 *Доступность номеров на сегодня:*\n\n",
        "avail_rooms":  {"Deluxe King": "Делюкс King", "Deluxe Twin": "Делюкс Twin", "Suite": "Люкс"},
        "avail_free":   "свободно",
        "manager_text": (
            "👨‍💼 *Связь с менеджером*\n\n"
            "📞 *+998 77 090 73 37*\n"
            "📞 *+998 (55) 515-07-07*\n"
            "✉️ medinatownhotel@gmail.com\n"
            "🕐 Режим работы: 24/7"
        ),
        "review_start":  "⭐ *Оставить отзыв*\n\nРасскажите о вашем пребывании:\n_(Отмена: /cancel)_",
        "review_rating": "Оцените пребывание от 1 до 5:\n⭐1 — Плохо  ⭐⭐⭐⭐⭐5 — Отлично",
        "review_done":   "🙏 *Спасибо за отзыв!*\n\n{stars} ({rating}/5)\n\nДо скорой встречи! 🏨",
        "review_err":    "Введите цифру от 1 до 5:",
        "cancel_msg":    "Отменено. Чем могу помочь? 😊",
        "lang_choose":   "🌐 Выберите язык / Choose language / Tilni tanlang:",
        "mybooking_none": "У вас нет активных бронирований.",
        "mybooking_title": "📋 *Ваши бронирования:*\n\n",
        "cancel_booking_ask": "Введите номер брони для отмены (например: 5):",
        "cancel_booking_done": "✅ Бронь #{bid} отменена.",
        "cancel_booking_fail": "❌ Бронь не найдена или уже отменена.",
        "confirm_words": ["да", "yes", "ha", "ok", "подтверждаю"],
        "booking_pending": (
            "⏳ *Заявка принята!*\n\n"
            "🎫 Номер заявки: *#{bid}*\n"
            "👤 {name}\n"
            "📞 {phone}\n"
            "🛏 {room}\n"
            "📅 {ci} → {co}\n"
            "🌙 {nights} ночей\n"
            "👥 {guests}\n"
            "💰 *{total}*\n\n"
            "⏳ Ожидайте подтверждения от менеджера.\n"
            "📞 +998 (55) 515-07-07"
        ),
        "booking_approved": "✅ Ваша бронь #{bid} *подтверждена* менеджером!\n\nДо встречи в Medinatown Hotel 🏨",
        "booking_rejected": "❌ Ваша бронь #{bid} *отклонена* менеджером.\n\nПожалуйста, свяжитесь с нами: +998 (55) 515-07-07",
    },
    "en": {
        "welcome": (
            "✨ Welcome to *Medinatown Hotel*, {name}!\n\n"
            "I'm your personal AI concierge, available 24/7.\n\n"
            "How can I help you?"
        ),
        "btn_book":    "📅 Book Room",
        "btn_info":    "ℹ️ Hotel Info",
        "btn_avail":   "🔍 Rooms",
        "btn_manager": "📞 Manager",
        "btn_review":  "⭐ Review",
        "btn_lang":    "🌐 Language",
        "info_text": (
            "🏨 *Medinatown Hotel*\n\n"
            "📍 58A Mukimi St, Tashkent\n"
            "📞 +998 (55) 515-07-07\n"
            "✉️ medinatownhotel@gmail.com\n"
            "🌐 medinatown.uz\n\n"
            "🛏 *Rooms (30 total):*\n"
            "• Deluxe King — 12 rooms, 24 m²\n"
            "• Deluxe Twin — 15 rooms, 18–24 m²\n"
            "• Suite King  —  3 rooms, 34 m²\n\n"
            "✅ *Amenities:* AC • Bathrobe • WiFi\n"
            "Smart TV • Safe • Hairdryer • Mini-bar • Breakfast\n\n"
            "🍽 *Restaurant* — 24/7, 60 seats\n"
            "🌇 *MINA Terrace* (5th fl.) — 11:00–05:00\n"
            "🍹 *Lobby Bar*\n\n"
            "🚗 4 km from airport • 5 km from station\n"
            "🚇 Novza metro — 2 km\n\n"
            "💳 VISA / MasterCard\n"
            "🎁 10% discount on website booking"
        ),
        "avail_title":  "🔍 *Room Availability Today:*\n\n",
        "avail_rooms":  {"Deluxe King": "Deluxe King", "Deluxe Twin": "Deluxe Twin", "Suite": "Suite"},
        "avail_free":   "available",
        "manager_text": (
            "👨‍💼 *Contact Manager*\n\n"
            "📞 *+998 77 090 73 37*\n"
            "📞 *+998 (55) 515-07-07*\n"
            "✉️ medinatownhotel@gmail.com\n"
            "🕐 Available: 24/7"
        ),
        "review_start":  "⭐ *Leave a Review*\n\nShare your experience:\n_(Cancel: /cancel)_",
        "review_rating": "Rate your stay 1–5:\n⭐1 — Poor  ⭐⭐⭐⭐⭐5 — Excellent",
        "review_done":   "🙏 *Thank you for your review!*\n\n{stars} ({rating}/5)\n\nSee you again! 🏨",
        "review_err":    "Please enter a number 1–5:",
        "cancel_msg":    "Cancelled. How can I help? 😊",
        "lang_choose":   "🌐 Выберите язык / Choose language / Tilni tanlang:",
        "mybooking_none": "You have no active bookings.",
        "mybooking_title": "📋 *Your bookings:*\n\n",
        "cancel_booking_ask": "Enter booking ID to cancel (e.g. 5):",
        "cancel_booking_done": "✅ Booking #{bid} cancelled.",
        "cancel_booking_fail": "❌ Booking not found or already cancelled.",
        "confirm_words": ["yes", "да", "ha", "ok"],
        "booking_pending": (
            "⏳ *Request received!*\n\n"
            "🎫 Booking ID: *#{bid}*\n"
            "👤 {name}\n"
            "📞 {phone}\n"
            "🛏 {room}\n"
            "📅 {ci} → {co}\n"
            "🌙 {nights} nights\n"
            "👥 {guests}\n"
            "💰 *{total}*\n\n"
            "⏳ Awaiting manager confirmation.\n"
            "📞 +998 (55) 515-07-07"
        ),
        "booking_approved": "✅ Your booking #{bid} has been *confirmed* by the manager!\n\nSee you at Medinatown Hotel 🏨",
        "booking_rejected": "❌ Your booking #{bid} was *declined* by the manager.\n\nPlease contact us: +998 (55) 515-07-07",
    },
    "uz": {
        "welcome": (
            "✨ *Medinatown Hotel*ga xush kelibsiz, {name}!\n\n"
            "Men sizning shaxsiy AI-konsyerjiingizman, 24/7.\n\n"
            "Qanday yordam bera olaman?"
        ),
        "btn_book":    "📅 Bron",
        "btn_info":    "ℹ️ Ma'lumot",
        "btn_avail":   "🔍 Xonalar",
        "btn_manager": "📞 Menejer",
        "btn_review":  "⭐ Sharh",
        "btn_lang":    "🌐 Til",
        "info_text": (
            "🏨 *Medinatown Hotel*\n\n"
            "📍 Mukimi ko'chasi 58A, Toshkent\n"
            "📞 +998 (55) 515-07-07\n"
            "✉️ medinatownhotel@gmail.com\n"
            "🌐 medinatown.uz\n\n"
            "🛏 *Xonalar (jami 30):*\n"
            "• Deluxe King — 12 xona, 24 m²\n"
            "• Deluxe Twin — 15 xona, 18–24 m²\n"
            "• Lyuks King  —  3 xona, 34 m²\n\n"
            "✅ *Qulayliklar:* Konditsioner • Xalat • WiFi\n"
            "Smart TV • Seyf • Fen • Mini-bar • Nonushta\n\n"
            "🍽 *Restoran* — 24/7, 60 o'rin\n"
            "🌇 *MINA Terrassa* (5 qavat) — 11:00–05:00\n"
            "🍹 *Lobby Bar*\n\n"
            "🚗 Aeroportdan 4 km • Vokzaldan 5 km\n"
            "🚇 Novza metro — 2 km\n\n"
            "💳 VISA / MasterCard\n"
            "🎁 Saytdan bronlasangiz 10% chegirma"
        ),
        "avail_title":  "🔍 *Bugungi xona mavjudligi:*\n\n",
        "avail_rooms":  {"Deluxe King": "Deluxe King", "Deluxe Twin": "Deluxe Twin", "Suite": "Lyuks"},
        "avail_free":   "bo'sh",
        "manager_text": (
            "👨‍💼 *Menejer bilan bog'lanish*\n\n"
            "📞 *+998 77 090 73 37*\n"
            "📞 *+998 (55) 515-07-07*\n"
            "✉️ medinatownhotel@gmail.com\n"
            "🕐 Ish vaqti: 24/7"
        ),
        "review_start":  "⭐ *Sharh qoldirish*\n\nTajribangizni baham ko'ring:\n_(Bekor: /cancel)_",
        "review_rating": "Qolishingizni 1–5 baho bering:\n⭐1 — Yomon  ⭐⭐⭐⭐⭐5 — A'lo",
        "review_done":   "🙏 *Sharhingiz uchun rahmat!*\n\n{stars} ({rating}/5)\n\nYana ko'rishguncha! 🏨",
        "review_err":    "1 dan 5 gacha raqam kiriting:",
        "cancel_msg":    "Bekor qilindi. Yordam bera olamanmi? 😊",
        "lang_choose":   "🌐 Выберите язык / Choose language / Tilni tanlang:",
        "mybooking_none": "Sizda faol bronlar yo'q.",
        "mybooking_title": "📋 *Sizning bronlaringiz:*\n\n",
        "cancel_booking_ask": "Bekor qilish uchun bron raqamini kiriting:",
        "cancel_booking_done": "✅ Bron #{bid} bekor qilindi.",
        "cancel_booking_fail": "❌ Bron topilmadi yoki allaqachon bekor qilingan.",
        "confirm_words": ["ha", "yes", "да", "ok"],
        "booking_pending": (
            "⏳ *Ariza qabul qilindi!*\n\n"
            "🎫 Bron raqami: *#{bid}*\n"
            "👤 {name}\n"
            "📞 {phone}\n"
            "🛏 {room}\n"
            "📅 {ci} → {co}\n"
            "🌙 {nights} kecha\n"
            "👥 {guests}\n"
            "💰 *{total}*\n\n"
            "⏳ Menejer tasdig'ini kuting.\n"
            "📞 +998 (55) 515-07-07"
        ),
        "booking_approved": "✅ #{bid}-bron menejer tomonidan *tasdiqlandi*!\n\nMedinatown Hotelda ko'rishguncha 🏨",
        "booking_rejected": "❌ #{bid}-bron menejer tomonidan *rad etildi*.\n\nIltimos bog'laning: +998 (55) 515-07-07",
    }
}

HOTEL_SYSTEM = """
You are a multilingual AI concierge for Medinatown Hotel in Tashkent.
Always respond in the SAME language the guest uses.
Be warm, professional, helpful — like a 5-star hotel concierge.
Hotel: Medinatown Hotel, 58A Mukimi St, Tashkent
Phone: +998 (55) 515-07-07 | Email: medinatownhotel@gmail.com
Rooms: Deluxe King $80/night (24m²), Deluxe Twin $70/night (18-24m²), Suite $150/night (34m²)
All rooms: AC, Smart TV, WiFi, safe, minibar, bathrobe, buffet breakfast included.
Restaurant 24/7 (60 seats), MINA Terrace 5th floor (11:00-05:00), Lobby Bar.
4km airport, 5km train station, Novza metro 2km.
For booking use the 📅 Бронировать button. For manager: 📞 Менеджер button.
"""

ROOM_CAPACITY = {"Deluxe King": 12, "Deluxe Twin": 15, "Suite": 3}
ROOM_PRICES_USD = {"Deluxe King": 80, "Deluxe Twin": 70, "Suite": 150}

chat_histories = {}
user_langs     = {}
spam_tracker   = {}  # uid -> [timestamps]

def get_lang(uid): return user_langs.get(uid, "ru")
def t(uid, key):
    lang = get_lang(uid)
    return T[lang].get(key, T["ru"].get(key, ""))

# ══════════════════════════════════════════════════════════════
#  ЦЕНЫ
# ══════════════════════════════════════════════════════════════
def get_usd_to_uzs() -> float:
    """Получить курс USD/UZS с ЦБ Узбекистана"""
    try:
        r = requests.get(
            "https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/",
            timeout=5
        )
        data = r.json()
        return float(data[0]["Rate"])
    except Exception as e:
        logger.warning(f"CBU rate fetch failed: {e}")
        return get_setting_float("usd_rate", 12700.0)

def get_room_prices() -> dict:
    """Вернуть цены в UZS — из Exely если включён, иначе из ЦБ"""
    if EXELY_ENABLED and EXELY_API_KEY:
        prices = fetch_exely_prices()
        if prices:
            return prices
    # Fallback: базовые USD × курс ЦБ
    rate = get_usd_to_uzs()
    save_setting("usd_rate", str(rate))
    return {k: int(v * rate) for k, v in ROOM_PRICES_USD.items()}

def fetch_exely_prices() -> dict | None:
    """Получить актуальные цены из Exely API"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        r = requests.get(
            f"https://api.exely.com/v1/hotels/{EXELY_HOTEL_ID}/rates",
            headers={"Authorization": f"Bearer {EXELY_API_KEY}"},
            params={"check_in": today, "check_out": tomorrow},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            prices = {}
            # Маппинг Exely room_type_id → наши типы (нужно уточнить у отеля)
            for room in data.get("rooms", []):
                name = room.get("name", "")
                price = room.get("price", 0)
                if "king" in name.lower() and "deluxe" in name.lower():
                    prices["Deluxe King"] = int(price)
                elif "twin" in name.lower():
                    prices["Deluxe Twin"] = int(price)
                elif "suite" in name.lower() or "luxe" in name.lower():
                    prices["Suite"] = int(price)
            return prices if prices else None
    except Exception as e:
        logger.error(f"Exely API error: {e}")
    return None

def format_price(uzs: int) -> str:
    """Форматировать цену: 850 000 сум"""
    return f"{uzs:,}".replace(",", " ") + " сум"

# ══════════════════════════════════════════════════════════════
#  БАЗА ДАННЫХ
# ══════════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect("hotel.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT, room_type TEXT,
        checkin TEXT, checkout TEXT, nights INTEGER,
        total_uzs INTEGER, total_usd INTEGER,
        adults INTEGER DEFAULT 1, children INTEGER DEFAULT 0,
        user_id INTEGER, username TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, username TEXT,
        rating INTEGER, text TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT
    )""")
    # Добавить колонки если их нет (миграция)
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN adults INTEGER DEFAULT 1")
    except: pass
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN children INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN total_uzs INTEGER DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN total_usd INTEGER DEFAULT 0")
    except: pass
    conn.commit()
    conn.close()

def get_setting(key, default=""): 
    conn = sqlite3.connect("hotel.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def get_setting_float(key, default=0.0):
    try: return float(get_setting(key, str(default)))
    except: return default

def save_setting(key, value):
    conn = sqlite3.connect("hotel.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()

def check_availability(room_type, checkin, checkout):
    conn = sqlite3.connect("hotel.db")
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) FROM bookings 
        WHERE room_type=? AND status IN ('pending','confirmed')
        AND NOT (checkout <= ? OR checkin >= ?)""",
        (room_type, checkin, checkout))
    booked = c.fetchone()[0]
    conn.close()
    return ROOM_CAPACITY.get(room_type, 0) - booked

def save_booking(name, phone, room_type, checkin, checkout,
                 nights, total_uzs, total_usd, adults, children, user_id, username):
    conn = sqlite3.connect("hotel.db")
    c = conn.cursor()
    c.execute("""INSERT INTO bookings 
        (name,phone,room_type,checkin,checkout,nights,
         total_uzs,total_usd,adults,children,user_id,username,status,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (name, phone, room_type, checkin, checkout, nights,
         total_uzs, total_usd, adults, children,
         user_id, username or "guest", "pending",
         datetime.now().strftime("%d.%m.%Y %H:%M")))
    bid = c.lastrowid
    conn.commit()
    conn.close()
    return bid

def get_booking(bid):
    conn = sqlite3.connect("hotel.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE id=?", (bid,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def update_booking_status(bid, status):
    conn = sqlite3.connect("hotel.db")
    c = conn.cursor()
    c.execute("UPDATE bookings SET status=? WHERE id=?", (status, bid))
    conn.commit()
    conn.close()

def get_user_bookings(user_id):
    conn = sqlite3.connect("hotel.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT * FROM bookings WHERE user_id=? AND status != 'cancelled' 
                 ORDER BY id DESC LIMIT 5""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_review(user_id, username, rating, text):
    conn = sqlite3.connect("hotel.db")
    c = conn.cursor()
    c.execute("INSERT INTO reviews (user_id,username,rating,text,created_at) VALUES (?,?,?,?,?)",
        (user_id, username or "guest", rating, text,
         datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ
# ══════════════════════════════════════════════════════════════
def is_spam(uid) -> bool:
    """Не более 10 запросов к AI в минуту"""
    now = datetime.now()
    times = spam_tracker.get(uid, [])
    times = [t for t in times if (now - t).seconds < 60]
    times.append(now)
    spam_tracker[uid] = times
    return len(times) > 10

async def notify_manager(app, text, reply_markup=None):
    mid = get_setting("manager_chat_id")
    if mid:
        try:
            await app.bot.send_message(
                chat_id=int(mid), text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Manager notify error: {e}")

def ask_gemini(uid, message) -> str:
    history = chat_histories.get(uid, [])
    prompt = HOTEL_SYSTEM + "\n\nCONVERSATION:\n"
    for m in history[-8:]:
        prompt += f"{m['role']}: {m['content']}\n"
    prompt += f"\nGuest: {message}\nConcierge:"
    try:
        r = requests.post(GEMINI_URL,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15)
        reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        if uid not in chat_histories:
            chat_histories[uid] = []
        chat_histories[uid].append({"role": "Guest", "content": message})
        chat_histories[uid].append({"role": "Concierge", "content": reply})
        if len(chat_histories[uid]) > 20:
            chat_histories[uid] = chat_histories[uid][-20:]
        return reply
    except Exception as e:
        logger.error(e)
        return "Извините, ошибка. / Sorry, error. / Xatolik."

def main_keyboard(uid):
    return ReplyKeyboardMarkup([
        [KeyboardButton(t(uid,"btn_book"), web_app=WebAppInfo(url=MINI_APP_URL)),
         KeyboardButton(t(uid,"btn_info"))],
        [KeyboardButton(t(uid,"btn_avail")),
         KeyboardButton(t(uid,"btn_manager"))],
        [KeyboardButton(t(uid,"btn_review")),
         KeyboardButton(t(uid,"btn_lang"))],
    ], resize_keyboard=True, is_persistent=True)

def booking_approve_kb(bid):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{bid}"),
        InlineKeyboardButton("❌ Отклонить",   callback_data=f"reject_{bid}"),
    ]])

def status_emoji(status):
    return {"pending": "⏳", "confirmed": "✅", "cancelled": "❌"}.get(status, "❓")

# ══════════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    uid  = update.effective_user.id
    name = update.effective_user.first_name or "Гость"
    await update.message.reply_text(
        t(uid,"welcome").format(name=name),
        parse_mode='Markdown',
        reply_markup=main_keyboard(uid)
    )

async def register_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    save_setting("manager_chat_id", cid)
    await update.message.reply_text(
        f"✅ Уведомления активированы!\nВаш Chat ID: `{cid}`\n\n"
        f"Теперь вы будете получать уведомления о новых бронях с кнопками подтверждения.",
        parse_mode='Markdown'
    )

async def cmd_mybooking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bookings = get_user_bookings(uid)
    if not bookings:
        await update.message.reply_text(t(uid,"mybooking_none"))
        return
    text = t(uid,"mybooking_title")
    for b in bookings:
        emoji = status_emoji(b['status'])
        uzs = format_price(b.get('total_uzs') or b.get('total',0))
        text += (
            f"{emoji} *#{b['id']}* — {b['room_type']}\n"
            f"📅 {b['checkin']} → {b['checkout']} ({b['nights']} н.)\n"
            f"💰 {uzs}\n\n"
        )
    # Кнопка отмены
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Отменить бронь", callback_data="cancel_my_booking")
    ]])
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    text = update.message.text

    for lang in ["ru","en","uz"]:
        tl = T[lang]
        if text == tl.get("btn_info"):
            await update.message.reply_text(t(uid,"info_text"), parse_mode='Markdown')
            return
        elif text == tl.get("btn_avail"):
            await send_availability(update, uid)
            return
        elif text == tl.get("btn_manager"):
            await update.message.reply_text(t(uid,"manager_text"), parse_mode='Markdown')
            return
        elif text == tl.get("btn_review"):
            await update.message.reply_text(t(uid,"review_start"), parse_mode='Markdown')
            context.user_data['state'] = 'review_text'
            return
        elif text == tl.get("btn_lang"):
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en"),
                InlineKeyboardButton("🇺🇿 O'zbek",  callback_data="setlang_uz"),
            ]])
            await update.message.reply_text(t(uid,"lang_choose"), reply_markup=kb)
            return

    # Состояния отзыва
    state = context.user_data.get('state')
    if state == 'review_text':
        context.user_data['review_text'] = text
        context.user_data['state'] = 'review_rating'
        await update.message.reply_text(t(uid,"review_rating"))
        return
    elif state == 'review_rating':
        try:
            rating = int(text.strip())
            if not 1 <= rating <= 5: raise ValueError
        except:
            await update.message.reply_text(t(uid,"review_err"))
            return
        u = update.effective_user
        save_review(u.id, u.username, rating, context.user_data.get('review_text',''))
        context.user_data.pop('state', None)
        stars = "⭐" * rating
        await update.message.reply_text(
            t(uid,"review_done").format(stars=stars, rating=rating),
            parse_mode='Markdown'
        )
        return
    elif state == 'cancel_booking_input':
        try:
            bid = int(text.strip())
            booking = get_booking(bid)
            if booking and booking['user_id'] == uid and booking['status'] != 'cancelled':
                update_booking_status(bid, 'cancelled')
                await update.message.reply_text(
                    t(uid,"cancel_booking_done").format(bid=bid))
            else:
                await update.message.reply_text(t(uid,"cancel_booking_fail"))
        except:
            await update.message.reply_text(t(uid,"cancel_booking_fail"))
        context.user_data.pop('state', None)
        return

    # AI консьерж
    if is_spam(uid):
        await update.message.reply_text("⏳ Подождите немного перед следующим сообщением.")
        return
    reply = ask_gemini(uid, text)
    await update.message.reply_text(reply)

async def send_availability(update, uid):
    today = datetime.now().strftime("%Y-%m-%d")
    today_iso = datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.now().strftime("%d.%m.%Y")
    prices = get_room_prices()
    room_names = t(uid,"avail_rooms")
    rate = get_usd_to_uzs()
    text = t(uid,"avail_title")
    text += f"💱 Курс: 1 USD = {int(rate):,} сум\n\n".replace(",","_").replace("_"," ")
    for rt in ["Deluxe King","Deluxe Twin","Suite"]:
        n   = check_availability(rt, today_iso, today_iso)
        e   = "✅" if n > 0 else "❌"
        rn  = room_names.get(rt, rt)
        uzs = format_price(prices.get(rt, 0))
        text += f"{e} *{rn}*\n    💰 {uzs}/ночь — {n} {t(uid,'avail_free')}\n\n"
    await update.message.reply_text(text, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    data = query.data

    if data.startswith("setlang_"):
        lang = data.split("_")[1]
        user_langs[uid] = lang
        name = query.from_user.first_name or "Гость"
        await query.message.reply_text(
            t(uid,"welcome").format(name=name),
            parse_mode='Markdown',
            reply_markup=main_keyboard(uid)
        )

    elif data.startswith("approve_"):
        bid     = int(data.split("_")[1])
        booking = get_booking(bid)
        if not booking:
            await query.edit_message_text("❌ Бронь не найдена.")
            return
        update_booking_status(bid, 'confirmed')
        # Уведомить гостя
        try:
            await context.bot.send_message(
                chat_id=booking['user_id'],
                text=T.get(user_langs.get(booking['user_id'],'ru'),T['ru'])['booking_approved'].format(bid=bid),
                parse_mode='Markdown'
            )
        except: pass
        await query.edit_message_text(
            f"✅ Бронь *#{bid}* подтверждена!\n\n"
            f"👤 {booking['name']} | 📞 {booking['phone']}\n"
            f"🛏 {booking['room_type']}\n"
            f"📅 {booking['checkin']} → {booking['checkout']}",
            parse_mode='Markdown'
        )

    elif data.startswith("reject_"):
        bid     = int(data.split("_")[1])
        booking = get_booking(bid)
        if not booking:
            await query.edit_message_text("❌ Бронь не найдена.")
            return
        update_booking_status(bid, 'cancelled')
        try:
            await context.bot.send_message(
                chat_id=booking['user_id'],
                text=T.get(user_langs.get(booking['user_id'],'ru'),T['ru'])['booking_rejected'].format(bid=bid),
                parse_mode='Markdown'
            )
        except: pass
        await query.edit_message_text(
            f"❌ Бронь *#{bid}* отклонена.\n\n"
            f"👤 {booking['name']} | {booking['room_type']}",
            parse_mode='Markdown'
        )

    elif data == "cancel_my_booking":
        context.user_data['state'] = 'cancel_booking_input'
        await query.message.reply_text(t(uid,"cancel_booking_ask"))

# ══════════════════════════════════════════════════════════════
#  MINI APP DATA
# ══════════════════════════════════════════════════════════════
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u   = update.effective_user
    try:
        data     = json.loads(update.message.web_app_data.data)
        prices   = get_room_prices()
        room_id  = data.get('room_id','')
        nights   = data.get('nights', 0)
        adults   = data.get('adults', 1)
        children = data.get('children', 0)

        # Пересчитать цену по актуальному курсу
        total_uzs = prices.get(room_id, 0) * nights
        total_usd = ROOM_PRICES_USD.get(room_id, 0) * nights

        bid = save_booking(
            data.get('name','Не указано'),
            data.get('phone','Не указан'),
            room_id,
            data.get('checkin',''),
            data.get('checkout',''),
            nights,
            total_uzs, total_usd,
            adults, children,
            u.id, u.username
        )

        guests_str = f"{adults} взр." + (f", {children} дет." if children > 0 else "")
        price_str  = f"{format_price(total_uzs)} (~${total_usd})"

        # Сообщение гостю
        await update.message.reply_text(
            t(uid,"booking_pending").format(
                bid=bid,
                name=data.get('name','—'),
                phone=data.get('phone','—'),
                room=data.get('room_name','—'),
                ci=data.get('checkin',''),
                co=data.get('checkout',''),
                nights=nights,
                guests=guests_str,
                total=price_str,
            ),
            parse_mode='Markdown'
        )

        # Уведомление менеджеру с кнопками
        await notify_manager(
            context.application,
            f"🔔 *НОВАЯ ЗАЯВКА #{bid}*\n\n"
            f"👤 {data.get('name','—')}\n"
            f"📞 {data.get('phone','—')}\n"
            f"🛏 {data.get('room_name','—')}\n"
            f"📅 {data.get('checkin','')} → {data.get('checkout','')}\n"
            f"🌙 {nights} ночей\n"
            f"👥 {guests_str}\n"
            f"💰 {price_str}\n"
            f"📱 @{u.username or 'нет username'}",
            reply_markup=booking_approve_kb(bid)
        )

    except Exception as e:
        logger.error(f"Web app data error: {e}")
        await update.message.reply_text("❌ Ошибка. Попробуйте ещё раз.")

# ══════════════════════════════════════════════════════════════
#  КОМАНДЫ
# ══════════════════════════════════════════════════════════════
async def cmd_info(update, context):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid,"info_text"), parse_mode='Markdown')

async def cmd_availability(update, context):
    uid = update.effective_user.id
    await send_availability(update, uid)

async def cmd_manager(update, context):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid,"manager_text"), parse_mode='Markdown')

async def cancel(update, context):
    uid = update.effective_user.id
    context.user_data.clear()
    await update.message.reply_text(t(uid,"cancel_msg"))

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",            start))
    app.add_handler(CommandHandler("info",             cmd_info))
    app.add_handler(CommandHandler("availability",     cmd_availability))
    app.add_handler(CommandHandler("manager",          cmd_manager))
    app.add_handler(CommandHandler("mybooking",        cmd_mybooking))
    app.add_handler(CommandHandler("cancel",           cancel))
    app.add_handler(CommandHandler("register_manager", register_manager))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))

    print("🏨 Medinatown Hotel Bot v3.0 запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
