import asyncio
import logging
import os
from datetime import datetime, date, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# ============================================================
#  SOZLAMALAR
# ============================================================
BOT_TOKEN           = "8957719366:AAHONxdOfjvZkbHAaOcBMUAjceG5cg7vwwI"
MUDIR_SECRET_CODE   = "1103"
GROUP_OR_CHANNEL_ID = int(os.getenv("GROUP_OR_CHANNEL_ID", "-100123456789"))

logging.basicConfig(level=logging.INFO)
router = Router()

TEACHERS_DB: dict[int, dict] = {}
MUDIR_IDS:   set[int]        = set()

# ============================================================
#  OCHIQ DARSLAR BAZASI (34 ta)
#  Bugungi sana: 2026-10-22
#  O'tib ketgan darslar (2026-10-22 gacha): 1-18 (18 ta)
#  Kelgusi darslar: 19-34 (16 ta)
# ============================================================
SCHEDULE_DB: list[dict] = [
    # ✅ O'TIB KETGAN DARSLAR (14-sen – 21-okt)
    {"date": "2026-09-14", "teacher": "Sobirov Aloviddin Abduraxmonovich",        "subject": "Jismoniy sifatlarga umumiy tavsif",                                                           "status": False},
    {"date": "2026-09-16", "teacher": "Shukurllayev Jurabek Maksadbayevich",       "subject": "Voleybol o'yinida tayyorgarlik turlarining o'rni va ahamiyati",                               "status": False},
    {"date": "2026-09-21", "teacher": "Nurmatov Farxat Abdualimovich",             "subject": "Jismoniy tarbiya va sportni boshqarishda asosiy qonun va manbalari",                         "status": False},
    {"date": "2026-09-21", "teacher": "Abdulaxadov Akromjon Ro'zmamatovich",       "subject": "Shisey turish shintay kurashda yurishlar",                                                    "status": False},
    {"date": "2026-09-22", "teacher": "Xonchayev Muxsinbek Muxtorovich",           "subject": "Yengil atletika turlaridan sakrash, uloqtirish va ko'pkurash",                               "status": False},
    {"date": "2026-09-29", "teacher": "Raximberdiyev Javlonbek Nasriddin o'g'li",  "subject": "Saf mashqlari tasnifi va bo'limi",                                                            "status": False},
    {"date": "2026-09-29", "teacher": "Odilov Otbek Norboyevich",                  "subject": "Yengil atletika turlaridan sakrash, uloqtirish va ko'pkurash turlari texnikasini o'rgatish", "status": False},
    {"date": "2026-09-30", "teacher": "Yusupbayeva Amangul Saparbayevna",          "subject": "Ob-havo va iqlim va unga moslashuv",                                                         "status": False},
    {"date": "2026-09-30", "teacher": "Tursunov Abdumo'min Erdiqulovich",          "subject": "Kuch qobiliyatini tarbiyalash",                                                               "status": False},
    {"date": "2026-09-30", "teacher": "Yo'ldoshev Zafar Shuxratovich",             "subject": "Mashg'ulot joylari va ularning jihozlanishi",                                                  "status": False},
    {"date": "2026-10-08", "teacher": "Tojiyev Muzafarjon Akbarovich",             "subject": "Jismoniy tarbiya va sport sohasida ta'lim tamoyillari",                                      "status": False},
    {"date": "2026-10-09", "teacher": "Nurmatov Farxat Abdualimovich",             "subject": "Jismoniy tarbiya va sportni boshqarish usullari",                                            "status": False},
    {"date": "2026-10-09", "teacher": "Raximberdiyev Javlonbek Nasriddin o'g'li",  "subject": "Akrobatika mashqlari",                                                                        "status": False},
    {"date": "2026-10-15", "teacher": "Abduraximov Sardor Dilmurod o'g'li",        "subject": "Saf mashqlari: orani ochish va yaqinlashtirish",                                              "status": False},
    {"date": "2026-10-20", "teacher": "Odilov Otbek Norboyevich",                  "subject": "Start va start oldi tezlanish",                                                               "status": False},
    {"date": "2026-10-21", "teacher": "Xonchayev Muxsinbek Muxtorovich",           "subject": "4x10 m va 4x20 m moksimon yugurish metodikasini o'rgatish",                                  "status": False},
    # 📅 BUGUN (2026-10-22)
    {"date": "2026-10-22", "teacher": "Abdamitova Kamola Kamiljanova",              "subject": "Sog'lom turmush tarzi va sport kiyimlari hamda poyabzallariga gigiyenik talablar",           "status": False},
    {"date": "2026-10-22", "teacher": "Abdamitova Kamola Kamiljanova",              "subject": "Jismoniy tarbiya vositalarining umumiy tavsifi",                                              "status": False},
    # 📅 KELGUSI DARSLAR
    {"date": "2026-10-28", "teacher": "Shukurllayev Jurabek Maksadbayevich",       "subject": "Ilmiy faoliyat mezonlari",                                                                   "status": False},
    {"date": "2026-11-02", "teacher": "Buvorayev Gulux Shoikrom qizi",             "subject": "Jismoniy sifatlarni tarbiyalash va rivojlantirish",                                          "status": False},
    {"date": "2026-11-03", "teacher": "Tojiyev Muzafarjon Akbarovich",             "subject": "Egiluvchanlik haqida tushuncha, turlari va o'lchov mezonlari",                               "status": False},
    {"date": "2026-11-04", "teacher": "Yo'ldoshev Zafar Shuxratovich",             "subject": "Qisqa masofaga yugurish texnikasini o'rgatish",                                               "status": False},
    {"date": "2026-11-05", "teacher": "Tursunov Abdumo'min Erdiqulovich",          "subject": "Harakatga o'rgatish bosqichlari",                                                             "status": False},
    {"date": "2026-11-07", "teacher": "Abdulaxadov Akromjon Ro'zmamatovich",       "subject": "Voleybol o'yinida hujum texnikasi",                                                           "status": False},
    {"date": "2026-11-09", "teacher": "Gimazuddinov Radik Galimovich",             "subject": "Organizatsiya raboti po opredeleniyu fizicheskoy podgotovlennosti naseleniya",                "status": False},
    {"date": "2026-11-19", "teacher": "Abduraximov Sardor Dilmurod o'g'li",        "subject": "Akrobatik mashqlar",                                                                          "status": False},
    {"date": "2026-11-20", "teacher": "Anorboyev Bekmurod Dilmurod o'gli",         "subject": "Estafetali yugurish texnikasini o'rgatish",                                                   "status": False},
    {"date": "2026-11-20", "teacher": "Anorboyev Bekmurod Dilmurod o'gli",         "subject": "Voleybol bo'yicha guruh o'rtasida musobaqani tashkil etish",                                  "status": False},
    {"date": "2026-11-27", "teacher": "Sobirov Aloviddin Abduraxmonovich",         "subject": "Yozgi Olimpiya o'yinlari",                                                                    "status": False},
    {"date": "2026-11-27", "teacher": "Zulxaydarov Javlonbek Abduqaxor o'g'li",   "subject": "Qadimgi Olimpiya o'yinlari",                                                                  "status": False},
    {"date": "2026-11-27", "teacher": "Zulxaydarov Javlonbek Abduqaxor o'g'li",   "subject": "Yozgi va qishki Olimpiya o'yinlari",                                                          "status": False},
    {"date": "2026-12-07", "teacher": "Yusupbayeva Amangul Saparbayevna",          "subject": "Estafeta o'yinlarini o'rgatish metodikasi",                                                   "status": False},
    {"date": "2026-12-15", "teacher": "Buvorayev Gulux Shoikrom qizi",             "subject": "Tabiatning sog'lomlashtiruvchi kuchlari, gigiyenik omillar va vositalar",                     "status": False},
    {"date": "2026-12-23", "teacher": "Gimazuddinov Radik Galimovich",             "subject": "Organizatsiya i provedenie sorevnovaniy po lègkoy atletike",                                  "status": False},
]

Q1_START = "2026-09-01"
Q1_END   = "2026-12-31"
Q2_START = "2027-01-01"

UNIQUE_TEACHERS: list[str] = sorted(set(item["teacher"] for item in SCHEDULE_DB))


# ============================================================
#  KLAVIATURALAR
# ============================================================

def teacher_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"t_{i}")]
        for i, name in enumerate(UNIQUE_TEACHERS)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def report_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Hisobot yuborish", callback_data="send_report")]
    ])


def mudir_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 1-chorak hisoboti (Sep–Dec 2026)", callback_data="mudir_q1")],
        [InlineKeyboardButton(text="📊 2-chorak hisoboti (Yan 2027+)",    callback_data="mudir_q2")],
    ])


# ============================================================
#  JADVAL VA HISOBOT GENERATORLARI
# ============================================================

def build_personal_schedule(t_name: str) -> str:
    today_str  = date.today().strftime("%Y-%m-%d")
    my_lessons = [item for item in SCHEDULE_DB if item["teacher"] == t_name]

    if not my_lessons:
        return "📭 Sizga belgilangan ochiq dars topilmadi."

    done_lines    = []
    pending_lines = []
    today_lines   = []
    coming_lines  = []

    for item in my_lessons:
        d    = item["date"]
        subj = item["subject"]
        if item["status"]:
            done_lines.append(f"  ✅ {d} — {subj}")
        elif d == today_str:
            today_lines.append(f"  🔴 {d} — {subj}  <b>(BUGUN!)</b>")
        elif d < today_str:
            pending_lines.append(f"  ❌ {d} — {subj}  <i>(hisobot topshirilmagan!)</i>")
        else:
            coming_lines.append(f"  📅 {d} — {subj}")

    parts = [f"📋 <b>Sizning ochiq darslaringiz:</b>\n<b>{t_name}</b>\n"]

    if today_lines:
        parts.append("🔴 <b>BUGUNGI DARS:</b>")
        parts.extend(today_lines)
        parts.append("")

    if pending_lines:
        parts.append(f"❌ <b>Hisobot kutilmoqda ({len(pending_lines)} ta):</b>")
        parts.extend(pending_lines)
        parts.append("")

    if done_lines:
        parts.append(f"✅ <b>Topshirilgan ({len(done_lines)} ta):</b>")
        parts.extend(done_lines)
        parts.append("")

    if coming_lines:
        parts.append(f"📅 <b>Kelgusi darslar ({len(coming_lines)} ta):</b>")
        parts.extend(coming_lines)

    return "\n".join(parts)


def build_mudir_quarter_report(quarter: int) -> str:
    if quarter == 1:
        lessons = [i for i in SCHEDULE_DB if Q1_START <= i["date"] <= Q1_END]
        header  = "📊 <b>1-CHORAK HISOBOTI (Sentyabr – Dekabr 2026)</b>\n"
    else:
        lessons = [i for i in SCHEDULE_DB if i["date"] >= Q2_START]
        if not lessons:
            return (
                "📊 <b>2-CHORAK HISOBOTI (Yanvar 2027+)</b>\n\n"
                "ℹ️ 2-chorak <b>2027-yil yanvar oyidan</b> boshlanadi.\n"
                "Hozircha bu chorakka darslar kiritilmagan."
            )
        header = "📊 <b>2-CHORAK HISOBOTI (Yanvar 2027+)</b>\n"

    today_str = date.today().strftime("%Y-%m-%d")
    done   = [i for i in lessons if i["status"]]
    missed = [i for i in lessons if not i["status"] and i["date"] < today_str]
    today_ = [i for i in lessons if i["date"] == today_str]
    coming = [i for i in lessons if i["date"] > today_str]

    total_past = len(done) + len(missed)
    pct = round(len(done) / total_past * 100) if total_past > 0 else 0

    lines = [
        header,
        f"✅ Hisobot topshirilgan:   <b>{len(done)}</b> ta",
        f"❌ Hisobot topshirilmagan: <b>{len(missed)}</b> ta",
        f"🔴 Bugungi darslar:        <b>{len(today_)}</b> ta",
        f"📅 Kutilayotgan darslar:   <b>{len(coming)}</b> ta",
        f"📈 Hisobot foizi:          <b>{pct}%</b>",
        f"━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    if today_:
        lines.append("🔴 <b>BUGUNGI DARSLAR:</b>")
        for i in today_:
            lines.append(f"  • {i['teacher']}")
            lines.append(f"    <i>{i['subject']}</i>")
        lines.append("")

    if missed:
        lines.append("❌ <b>Topshirilmaganlar (muddati o'tgan):</b>")
        for i in missed:
            lines.append(f"  • {i['date']} — {i['teacher']}")
            lines.append(f"    <i>{i['subject']}</i>")
        lines.append("")

    if done:
        lines.append("✅ <b>Topshirilganlar:</b>")
        for i in done:
            lines.append(f"  • {i['date']} — {i['teacher']}")
            lines.append(f"    <i>{i['subject']}</i>")
        lines.append("")

    if coming:
        lines.append("📅 <b>Kelgusi darslar:</b>")
        for i in coming:
            lines.append(f"  • {i['date']} — {i['teacher']}")
            lines.append(f"    <i>{i['subject']}</i>")

    return "\n".join(lines)


# ============================================================
#  HOLAT MASHINALARI
# ============================================================

class BotStates(StatesGroup):
    waiting_for_mudir_code = State()
    waiting_for_report     = State()


# ============================================================
#  HANDLERLAR
# ============================================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍🏫 O'qituvchi bo'lib ro'yxatdan o'tish", callback_data="reg_teacher")],
        [InlineKeyboardButton(text="🔐 Kafedra mudiri bo'lib kirish",           callback_data="reg_mudir")],
    ])
    await message.answer(
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        "Jismoniy madaniyat nazariyasi kafedrasining ochiq darslarni "
        "nazorat qiluvchi botiga xush kelibsiz.\n\n"
        "Iltimos, o'z rolingizni tanlang:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "reg_mudir")
async def cb_reg_mudir(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Kafedra mudiri sifatida kirish uchun maxsus kodni kiriting:")
    await state.set_state(BotStates.waiting_for_mudir_code)
    await callback.answer()


@router.message(BotStates.waiting_for_mudir_code)
async def check_mudir_code(message: Message, state: FSMContext):
    if (message.text or "").strip() == MUDIR_SECRET_CODE:
        MUDIR_IDS.add(message.from_user.id)
        await message.answer(
            "✅ Xush kelibsiz, <b>Mudirim</b>!\n\n"
            "Men sizga kafedradagi barcha ochiq darslar bo'yicha "
            "ma'lumotlarni uzatib turaman:\n\n"
            "📌 Har kuni o'qituvchilarga ertangi dars eslatmasini avtomatik yuboraman\n"
            "📌 O'tib ketgan darslar uchun hisobot talab qilinadi\n"
            "📌 Barcha hisobotlar to'g'ridan-to'g'ri sizga yo'naltiriladi\n\n"
            "Quyidan kerakli chorak hisobotini tanlang:",
            reply_markup=mudir_main_keyboard(),
        )
        await state.clear()
    else:
        await message.answer("❌ Xato kod! Qaytadan urinib ko'ring.")


@router.callback_query(F.data == "mudir_q1")
async def cb_mudir_q1(callback: CallbackQuery):
    if callback.from_user.id not in MUDIR_IDS:
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    await callback.message.answer(build_mudir_quarter_report(1), reply_markup=mudir_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "mudir_q2")
async def cb_mudir_q2(callback: CallbackQuery):
    if callback.from_user.id not in MUDIR_IDS:
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    await callback.message.answer(build_mudir_quarter_report(2), reply_markup=mudir_main_keyboard())
    await callback.answer()


@router.message(Command("hisobot"))
async def cmd_hisobot(message: Message):
    if message.from_user.id not in MUDIR_IDS:
        await message.answer("⛔ Bu buyruq faqat Kafedra mudiri uchun.")
        return
    await message.answer("Qaysi chorak hisobotini ko'rmoqchisiz?", reply_markup=mudir_main_keyboard())


@router.callback_query(F.data == "reg_teacher")
async def cb_reg_teacher(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Ro'yxatdan o'tish uchun o'z F.I.SH. ingizni tanlang:",
        reply_markup=teacher_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("t_"))
async def cb_save_teacher(callback: CallbackQuery):
    idx = int(callback.data[2:])
    if idx >= len(UNIQUE_TEACHERS):
        await callback.answer("Xato! Iltimos qaytadan /start bosing.")
        return

    name = UNIQUE_TEACHERS[idx]
    TEACHERS_DB[callback.from_user.id] = {"name": name}

    await callback.message.answer(
        f"✅ Rahmat, <b>{name}</b>!\n"
        "Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n"
        "🔔 Bot sizga:\n"
        "  • Kelgusi darslaringizni <b>1 kun oldin</b> eslatadi\n"
        "  • O'tib ketgan darslar uchun <b>hisobot talab qiladi</b>"
    )

    today_str = date.today().strftime("%Y-%m-%d")
    has_pending = any(
        item["teacher"] == name and item["date"] <= today_str and not item["status"]
        for item in SCHEDULE_DB
    )
    await callback.message.answer(
        build_personal_schedule(name),
        reply_markup=report_keyboard() if has_pending else None,
    )
    await callback.answer()


@router.message(Command("mening_darslarim"))
async def cmd_my_lessons(message: Message):
    if message.from_user.id not in TEACHERS_DB:
        await message.answer("⚠️ Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
        return
    t_name    = TEACHERS_DB[message.from_user.id]["name"]
    today_str = date.today().strftime("%Y-%m-%d")
    has_pending = any(
        item["teacher"] == t_name and item["date"] <= today_str and not item["status"]
        for item in SCHEDULE_DB
    )
    await message.answer(
        build_personal_schedule(t_name),
        reply_markup=report_keyboard() if has_pending else None,
    )


@router.callback_query(F.data == "send_report")
async def cb_ask_report(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Iltimos, ochiq darsingiz bo'yicha hisobotingizni yuboring\n"
        "(matn, rasm, fayl yoki hujjat):"
    )
    await state.set_state(BotStates.waiting_for_report)
    await callback.answer()


@router.message(BotStates.waiting_for_report)
async def receive_report(message: Message, state: FSMContext, bot: Bot):
    user         = message.from_user
    teacher_info = TEACHERS_DB.get(user.id, {"name": user.full_name})
    t_name       = teacher_info["name"]

    today_str = date.today().strftime("%Y-%m-%d")
    for item in SCHEDULE_DB:
        if item["teacher"] == t_name and item["date"] <= today_str:
            item["status"] = True

    username_part = f"@{user.username}" if user.username else f"ID:{user.id}"
    report_header = (
        f"📥 <b>Yangi ochiq dars hisoboti!</b>\n\n"
        f"👤 <b>O'qituvchi:</b> {t_name} ({username_part})\n"
        f"📅 <b>Vaqti:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"📝 <b>Hisobot quyida:</b>"
    )

    for mudir_id in MUDIR_IDS:
        try:
            await bot.send_message(mudir_id, report_header)
            await message.forward(mudir_id)
        except Exception as e:
            logging.warning(f"Mudirga yuborishda xato ({mudir_id}): {e}")

    await message.answer(
        "✅ Hisobotingiz qabul qilindi va Kafedra mudiriga yo'naltirildi!\n\n"
        "Jadvalingizni ko'rish uchun: /mening_darslarim"
    )
    await state.clear()


# ============================================================
#  KUNLIK ESLATMA VAZIFASI
# ============================================================

async def daily_scheduler(bot: Bot):
    while True:
        today     = date.today()
        today_str = today.strftime("%Y-%m-%d")
        tomorrow  = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        for item in SCHEDULE_DB:
            d_date = item["date"]
            t_name = item["teacher"]

            # Ertaga dars bor — guruh + o'qituvchiga eslatma
            if d_date == tomorrow:
                group_msg = (
                    f"🔔 <b>DIQQAT! ERTAGA OCHIQ DARS BOR!</b>\n\n"
                    f"📅 <b>Sana:</b> {d_date}\n"
                    f"👨‍🏫 <b>Ustoz:</b> {t_name}\n"
                    f"📚 <b>Mavzu:</b> {item['subject']}\n\n"
                    "Barcha mas'ullarni ogohlantiramiz!"
                )
                try:
                    await bot.send_message(GROUP_OR_CHANNEL_ID, group_msg)
                except Exception as e:
                    logging.warning(f"Guruhga yuborishda xato: {e}")

                for t_id, t_data in TEACHERS_DB.items():
                    if t_data["name"] == t_name:
                        try:
                            await bot.send_message(
                                t_id,
                                f"⚠️ <b>Eslatma!</b>\n\n"
                                f"Ertaga (<b>{d_date}</b>) sizning ochiq darsingiz bor:\n\n"
                                f"📚 <b>{item['subject']}</b>\n\n"
                                "Tayyorgarlik ko'rishingizni so'raymiz! 🎯"
                            )
                        except Exception as e:
                            logging.warning(f"O'qituvchiga eslatma xato ({t_id}): {e}")

            # O'tib ketgan, hisobot topshirilmagan
            if d_date < today_str and not item["status"]:
                for t_id, t_data in TEACHERS_DB.items():
                    if t_data["name"] == t_name:
                        try:
                            await bot.send_message(
                                t_id,
                                f"⚠️ <b>HISOBOT TALAB ETILADI!</b>\n\n"
                                f"Hurmatli <b>{t_name}</b>,\n"
                                f"<b>{d_date}</b> kuni bo'lib o'tgan ochiq dars:\n"
                                f"📚 <i>{item['subject']}</i>\n\n"
                                "bo'yicha hisobot hali topshirilmagan!\n"
                                "Iltimos, zudlik bilan yuborishingizni so'raymiz.",
                                reply_markup=report_keyboard(),
                            )
                        except Exception as e:
                            logging.warning(f"Hisobot eslatmasida xato ({t_id}): {e}")

        await asyncio.sleep(86400)


# ============================================================
#  ASOSIY ISHGA TUSHIRISH
# ============================================================

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)
    asyncio.create_task(daily_scheduler(bot))
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("✅ Bot ishga tushdi! 34 ta ochiq dars bazasi yuklandi. Sana: 2026-10-22")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
