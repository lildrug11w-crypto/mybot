
import os
import sqlite3
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("8596155663:AAF39l6ghcWAgTKBzEMq4wzCxhOAWod1WX0", "")
OWNER_ID = 8823742565
CARD = "4400430019265054"
CARD_NAME = "Қуандық С."

DONATES = {
    "100": ("100BS", 100),
    "200": ("200BS", 200),
    "1000": ("1000BS", 850),
    "5000": ("5000BS", 2250),
    "10000": ("10.000BS", 4500),
    "20000": ("20.000BS", 6700),
    "40000": ("40.000BS", 8000),
}

DB = "bot.db"
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def db():
    return sqlite3.connect(DB)


def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        bs TEXT NOT NULL,
        price INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS support (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        admin_id INTEGER,
        question TEXT,
        answer TEXT,
        created_at TEXT NOT NULL
    )""")
    con.commit()
    con.close()


def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    con = db()
    row = con.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,)).fetchone()
    con.close()
    return row is not None


def main_kb(user_id: int):
    rows = [
        [InlineKeyboardButton(text="💰 Қайырымдылық сатып алу", callback_data="donate")],
        [InlineKeyboardButton(text="📜 Сатып алу тарихы", callback_data="history")],
        [InlineKeyboardButton(text="🆘 Техникалық қолдау", callback_data="support")],
    ]
    if is_admin(user_id):
        rows.append([InlineKeyboardButton(text="⚙️ Әкімші панелі", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def donate_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="100BS — 100 ₸", callback_data="buy:100")],
        [InlineKeyboardButton(text="200BS — 200 ₸", callback_data="buy:200")],
        [InlineKeyboardButton(text="1000BS — 850 ₸", callback_data="buy:1000")],
        [InlineKeyboardButton(text="5000BS — 2250 ₸", callback_data="buy:5000")],
        [InlineKeyboardButton(text="10.000BS — 4500 ₸", callback_data="buy:10000")],
        [InlineKeyboardButton(text="20.000BS — 6700 ₸", callback_data="buy:20000")],
        [InlineKeyboardButton(text="40.000BS — 8000 ₸", callback_data="buy:40000")],
        [InlineKeyboardButton(text="⬅️ Артқа", callback_data="back")],
    ])


def payment_kb(purchase_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Төлемді растау", callback_data=f"confirm:{purchase_id}")],
        [InlineKeyboardButton(text="⬅️ Артқа", callback_data="donate")],
    ])


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Күтудегі төлемдер", callback_data="admin_pending")],
        [InlineKeyboardButton(text="👥 Әкімші қосу", callback_data="admin_add")],
        [InlineKeyboardButton(text="🚫 Әкімшіні өшіру", callback_data="admin_del")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⬅️ Артқа", callback_data="back")],
    ])


def payment_manage_kb(purchase_id: int, user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Орындау", callback_data=f"done:{purchase_id}:{user_id}"),
            InlineKeyboardButton(text="❌ Бас тарту", callback_data=f"reject:{purchase_id}:{user_id}")
        ]
    ])


class States(StatesGroup):
    waiting_receipt = State()
    waiting_support = State()
    waiting_admin_reply = State()
    waiting_add_admin = State()
    waiting_del_admin = State()


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "🇰🇿 <b>Қош келдіңіз!</b>\n\n"
        "CRMP жобасының ресми донат боты.\n"
        "Қажетті бөлімді таңдаңыз:"
    )
    await message.answer(text, reply_markup=main_kb(message.from_user.id), parse_mode="HTML")


@dp.callback_query(F.data == "donate")
async def donate(call: CallbackQuery):
    await call.message.edit_text(
        "💰 <b>Қайырымдылық сатып алу</b>\n\nДонат көлемін таңдаңыз:",
        reply_markup=donate_kb(), parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery):
    key = call.data.split(":")[1]
    bs, price = DONATES[key]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO purchases(user_id,username,bs,price,status,created_at) VALUES(?,?,?,?,?,?)",
        (call.from_user.id, call.from_user.username or "", bs, price, "қарастырылуда", now)
    )
    purchase_id = cur.lastrowid
    con.commit()
    con.close()

    text = (
        f"💳 <b>Төлем реквизиттері</b>\n\n"
        f"Карта: <code>{CARD}</code>\n"
        f"Алушы: <b>{CARD_NAME}</b>\n"
        f"Сома: <b>{price} ₸</b>\n"
        f"Донат: <b>{bs}</b>\n\n"
        "Төлемді жасап болған соң төмендегі батырманы басып, чек скриншотын жіберіңіз."
    )
    await call.message.edit_text(text, reply_markup=payment_kb(purchase_id), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data.startswith("confirm:"))
async def confirm(call: CallbackQuery, state: FSMContext):
    purchase_id = int(call.data.split(":")[1])
    con = db()
    row = con.execute(
        "SELECT bs,price,status FROM purchases WHERE id=? AND user_id=?",
        (purchase_id, call.from_user.id)
    ).fetchone()
    con.close()
    if not row:
        await call.answer("Тапсырыс табылмады.", show_alert=True)
        return
    if row[2] != "қарастырылуда":
        await call.answer("Бұл тапсырыс бұрын өңделген.", show_alert=True)
        return
    await state.update_data(purchase_id=purchase_id)
    await state.set_state(States.waiting_receipt)
    await call.message.answer(
        "📸 <b>Чекті жіберіңіз</b>\n\nТөлем жасалғанын растайтын скриншотты осы чатқа жіберіңіз.",
        parse_mode="HTML"
    )
    await call.answer()


@dp.message(States.waiting_receipt, F.photo)
async def receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    purchase_id = data.get("purchase_id")
    con = db()
    row = con.execute(
        "SELECT bs,price FROM purchases WHERE id=? AND user_id=?",
        (purchase_id, message.from_user.id)
    ).fetchone()
    con.close()
    if not row:
        await state.clear()
        await message.answer("Тапсырыс табылмады.")
        return

    caption = (
        "🧾 <b>Жаңа төлем чегі</b>\n\n"
        f"👤 ID: <code>{message.from_user.id}</code>\n"
        f"🔹 Username: @{message.from_user.username or 'жоқ'}\n"
        f"💰 Донат: <b>{row[0]}</b>\n"
        f"💵 Сома: <b>{row[1]} ₸</b>\n"
        f"🆔 Тапсырыс: <code>#{purchase_id}</code>"
    )
    await bot.send_photo(
        OWNER_ID,
        message.photo[-1].file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=payment_manage_kb(purchase_id, message.from_user.id)
    )
    await message.answer(
        "✅ Чек әкімшіге жіберілді.\n\n"
        "Тапсырыстың мәртебесін «Сатып алу тарихы» бөлімінен тексере аласыз."
    )
    await state.clear()


@dp.message(States.waiting_receipt)
async def receipt_wrong(message: Message):
    await message.answer("📸 Скриншотты <b>фото</b> ретінде жіберіңіз.", parse_mode="HTML")


@dp.callback_query(F.data == "history")
async def history(call: CallbackQuery):
    con = db()
    rows = con.execute(
        "SELECT bs,price,status,created_at FROM purchases WHERE user_id=? ORDER BY id DESC LIMIT 15",
        (call.from_user.id,)
    ).fetchall()
    con.close()
    if not rows:
        text = "📜 <b>Сатып алу тарихы</b>\n\nӘзірге сатып алулар жоқ."
    else:
        lines = ["📜 <b>Сатып алу тарихы</b>\n"]
        for bs, price, status, created in rows:
            lines.append(f"• {bs} — {price} ₸\n  Мәртебесі: <b>{status}</b>\n  {created}")
        text = "\n".join(lines)
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Артқа", callback_data="back")]]
    ), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "support")
async def support(call: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_support)
    await call.message.answer(
        "🆘 <b>Техникалық қолдау</b>\n\nСұрағыңызды бір хабарлама ретінде жазыңыз. Ол әкімшіге жіберіледі.",
        parse_mode="HTML"
    )
    await call.answer()


@dp.message(States.waiting_support)
async def support_message(message: Message, state: FSMContext):
    text = message.text or message.caption or "Медиа хабарлама"
    con = db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO support(user_id,question,created_at) VALUES(?,?,?)",
        (message.from_user.id, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    ticket_id = cur.lastrowid
    con.commit()
    con.close()

    admin_text = (
        "🆘 <b>Жаңа қолдау сұрауы</b>\n\n"
        f"👤 ID: <code>{message.from_user.id}</code>\n"
        f"🔹 @{message.from_user.username or 'жоқ'}\n"
        f"🎫 Тикет: <code>#{ticket_id}</code>\n\n"
        f"💬 {text}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Жауап беру", callback_data=f"reply:{ticket_id}:{message.from_user.id}")]
    ])
    await bot.send_message(OWNER_ID, admin_text, reply_markup=kb, parse_mode="HTML")
    await message.answer("✅ Хабарлама әкімшіге жіберілді. Жауапты күтіңіз.")
    await state.clear()


@dp.callback_query(F.data.startswith("reply:"))
async def reply_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Рұқсат жоқ.", show_alert=True)
        return
    _, ticket_id, user_id = call.data.split(":")
    await state.update_data(ticket_id=int(ticket_id), target_user=int(user_id))
    await state.set_state(States.waiting_admin_reply)
    await call.message.answer("✉️ Пайдаланушыға жіберілетін жауапты жазыңыз.")
    await call.answer()


@dp.message(States.waiting_admin_reply)
async def admin_reply(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    target = data["target_user"]
    ticket_id = data["ticket_id"]
    answer = message.text or message.caption or "Медиа хабарлама"
    try:
        await bot.send_message(
            target,
            f"🆘 <b>Әкімшінің жауабы</b>\n\n{answer}",
            parse_mode="HTML"
        )
        con = db()
        con.execute("UPDATE support SET answer=?, admin_id=? WHERE id=?",
                    (answer, message.from_user.id, ticket_id))
        con.commit()
        con.close()
        await message.answer("✅ Жауап пайдаланушыға жіберілді.")
    except Exception as e:
        await message.answer("❌ Пайдаланушыға хабарлама жіберу мүмкін болмады.")
    await state.clear()


@dp.callback_query(F.data == "admin")
async def admin(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Рұқсат жоқ.", show_alert=True)
        return
    await call.message.edit_text("⚙️ <b>Әкімші панелі</b>\n\nБөлімді таңдаңыз:",
                                 reply_markup=admin_kb(), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "admin_pending")
async def admin_pending(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    con = db()
    rows = con.execute(
        "SELECT id,user_id,username,bs,price,created_at FROM purchases "
        "WHERE status='қарастырылуда' ORDER BY id DESC LIMIT 20"
    ).fetchall()
    con.close()
    if not rows:
        text = "📋 Күтудегі төлемдер жоқ."
        kb = admin_kb()
        await call.message.edit_text(text, reply_markup=kb)
        await call.answer()
        return

    await call.message.edit_text("📋 <b>Күтудегі төлемдер</b>", parse_mode="HTML")
    for pid, uid, username, bs, price, created in rows:
        await call.message.answer(
            f"🆔 #{pid}\n👤 <code>{uid}</code> @{username or 'жоқ'}\n"
            f"💰 {bs} — {price} ₸\n🕐 {created}",
            reply_markup=payment_manage_kb(pid, uid),
            parse_mode="HTML"
        )
    await call.answer()


@dp.callback_query(F.data.startswith("done:"))
async def done(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    _, pid, uid = call.data.split(":")
    con = db()
    row = con.execute("SELECT bs,price FROM purchases WHERE id=?", (int(pid),)).fetchone()
    con.execute("UPDATE purchases SET status='орындалды' WHERE id=?", (int(pid),))
    con.commit()
    con.close()
    if row:
        await bot.send_message(int(uid),
            f"✅ Сатып алуыңыз орындалды!\n\n💰 {row[0]} — {row[1]} ₸\n"
            "Мәртебесі: <b>орындалды</b>", parse_mode="HTML")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("Орындалды")


@dp.callback_query(F.data.startswith("reject:"))
async def reject(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    _, pid, uid = call.data.split(":")
    con = db()
    con.execute("UPDATE purchases SET status='бас тартылды' WHERE id=?", (int(pid),))
    con.commit()
    con.close()
    await bot.send_message(int(uid),
        "❌ Төлеміңізден бас тартылды.\n\nҚате болса, техникалық қолдауға жазыңыз.")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("Бас тартылды")


@dp.callback_query(F.data == "admin_add")
async def admin_add(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("Бұл бөлім тек негізгі әкімшіге қолжетімді.", show_alert=True)
        return
    await state.set_state(States.waiting_add_admin)
    await call.message.answer("👥 Әкімші еткіңіз келетін пайдаланушының Telegram ID нөмірін жіберіңіз.")
    await call.answer()


@dp.message(States.waiting_add_admin)
async def admin_add_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        await state.clear()
        return
    try:
        uid = int(message.text.strip())
        con = db()
        con.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (uid,))
        con.commit()
        con.close()
        await message.answer(f"✅ <code>{uid}</code> әкімші ретінде қосылды.", parse_mode="HTML")
    except:
        await message.answer("❌ Дұрыс Telegram ID жіберіңіз.")
    await state.clear()


@dp.callback_query(F.data == "admin_del")
async def admin_del(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("Бұл бөлім тек негізгі әкімшіге қолжетімді.", show_alert=True)
        return
    await state.set_state(States.waiting_del_admin)
    await call.message.answer("🚫 Өшірілетін әкімшінің Telegram ID нөмірін жіберіңіз.")
    await call.answer()


@dp.message(States.waiting_del_admin)
async def admin_del_save(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        await state.clear()
        return
    try:
        uid = int(message.text.strip())
        if uid == OWNER_ID:
            await message.answer("❌ Негізгі әкімшіні өшіру мүмкін емес.")
        else:
            con = db()
            con.execute("DELETE FROM admins WHERE user_id=?", (uid,))
            con.commit()
            con.close()
            await message.answer(f"✅ <code>{uid}</code> әкімшілер тізімінен өшірілді.", parse_mode="HTML")
    except:
        await message.answer("❌ Дұрыс Telegram ID жіберіңіз.")
    await state.clear()


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    con = db()
    total = con.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
    pending = con.execute("SELECT COUNT(*) FROM purchases WHERE status='қарастырылуда'").fetchone()[0]
    done_count = con.execute("SELECT COUNT(*) FROM purchases WHERE status='орындалды'").fetchone()[0]
    con.close()
    await call.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"Барлық тапсырыс: <b>{total}</b>\n"
        f"Қарастырылуда: <b>{pending}</b>\n"
        f"Орындалды: <b>{done_count}</b>",
        reply_markup=admin_kb(), parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "🇰🇿 <b>Басты мәзір</b>\n\nҚажетті бөлімді таңдаңыз:",
        reply_markup=main_kb(call.from_user.id), parse_mode="HTML"
    )
    await call.answer()


@dp.message(Command("id"))
async def get_id(message: Message):
    await message.answer(f"🆔 Сіздің Telegram ID: <code>{message.from_user.id}</code>", parse_mode="HTML")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN орнатылмаған.")
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
