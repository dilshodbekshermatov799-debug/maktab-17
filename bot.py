import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import openpyxl

TOKEN = "9062629462:AAGF1OPCnRq9-YgODo3QUdxAl-HMSEi7xig"  # <-- BotFather'dan olgan tokeningizni kiriting
DB_NAME = "school_bot.db"

# --- RAHBARLARNING TELEGRAM ID LARI (Direktor va Zauch) ---
ADMIN_IDS = [473996412, 273054481, 592423188, 1377410511]  # <-- Haqiqiy Telegram ID raqamlaringizni yozing

# --- SINFLAR RO'YXATI ---
CLASSES_LIST = [
    "1-A", "1-B", "1-V", "1-G", "1-D",
    "2-A", "2-B", "2-V", "2-G", "2-D",
    "3-A", "3-B", "3-V", "3-D",
    "4-A", "4-B", "4-V", "4-D",
    "5-A", "5-B", "5-V", "5-D",
    "6-A", "6-B", "6-V", "6-D",
    "7-A", "7-B", "7-V", "7-D",
    "8-A", "8-B", "8-V", "8-D",
    "9-A", "9-B", "9-V", "9-D",
    "10-A", "10-B", "10-V",
    "11-A", "11-B", "11-V"
]

# --- RASMIY O'QITUVCHILAR BAZASI ---
OFFICIAL_TEACHERS = [
    {"name": "Qo'chqarov Akram", "subject": "Ona tili va adabiyoti"},
    {"name": "Roziqova Matluba", "subject": "Ona tili va adabiyoti"},
    {"name": "Nuriddinova Dilorom", "subject": "Ona tili va adabiyoti"},
    {"name": "Yunusova Saida", "subject": "Ona tili va adabiyoti"},
    {"name": "Mahmudjonova Madina", "subject": "Ona tili va adabiyoti"},
    {"name": "Abdullayeva Dilshoda", "subject": "Ona tili va adabiyoti"},
    {"name": "Vohidova Madina", "subject": "Ona tili va adabiyoti"},
    {"name": "Bekmirzayeva Shodiya", "subject": "Ona tili va adabiyoti"},
    {"name": "Bekmirzayeva Shaxnoza", "subject": "Ona tili va adabiyoti"},
    {"name": "Yakubboyeva Nilufar", "subject": "Rus tili va adabiyoti"},
    {"name": "Onorova Feruza", "subject": "Rus tili va adabiyoti"},
    {"name": "Axmedov Shoxobiddin", "subject": "Rus tili va adabiyoti"},
    {"name": "Akbaraliyeva Dilorom", "subject": "Rus tili va adabiyoti"},
    {"name": "Abdumuxtorova Feruza", "subject": "Rus tili va adabiyoti"},
    {"name": "Nizomov Rasuljon", "subject": "Rus tili va adabiyoti"},
    {"name": "G`ulomjonova Mushtariy", "subject": "Rus tili va adabiyoti"},
    {"name": "Yigitaliyeva Mushtariy", "subject": "Rus tili va adabiyoti"},
    {"name": "Sharifjonova Muhlisa", "subject": "Rus tili va adabiyoti"},
    {"name": "Ergashev Bahodir", "subject": "Rus tili va adabiyoti"},
    {"name": "Abdulazizova Mahliyo", "subject": "Ingiliz Tili"},
    {"name": "Boyzaqov Azizbek", "subject": "Ingiliz Tili"},
    {"name": "Shamsutdinova Dilnoza", "subject": "Ingiliz Tili"},
    {"name": "G'ulomqodirova Feruza", "subject": "Ingiliz Tili"},
    {"name": "Shermatov Dilshodbek", "subject": "Ingiliz Tili"},
    {"name": "Abdubannayeva Dildora", "subject": "Ingiliz Tili"},
    {"name": "Soliyev Abdugaffur", "subject": "Ingiliz tili"},
    {"name": "Xusanboyeva Oygul", "subject": "Ingiliz tili"},
    {"name": "Abdullayeva Muxlisa", "subject": "Ingiliz tili"},
    {"name": "Raxmonjonova Gulsanam", "subject": "Ingiliz Tili"},
    {"name": "Murodova Gulbahor", "subject": "Tarix"},
    {"name": "O`rinova Gulchehra", "subject": "Tarix"},
    {"name": "Sulaymonov Odiljon", "subject": "Tarix"},
    {"name": "Xakimova Mashhura", "subject": "Tarix"},
    {"name": "Usmonov Abrorbek", "subject": "Tarix"},
    {"name": "Nizomov Doniyor", "subject": "Iqtisod"},
    {"name": "Mamajonov Jasur", "subject": "Tarix"},
    {"name": "Iloviddinova Umida", "subject": "Tarbiya"},
    {"name": "Nuriddinov Humoyun", "subject": "Huquq-tarbiya"},
    {"name": "Jo`rayeva Gulchehra", "subject": "Matematika"},
    {"name": "Haydarov Kozimjon", "subject": "Matematika"},
    {"name": "Halilova Mahmuda", "subject": "Matematika"},
    {"name": "Yunusova Feruza", "subject": "Matematika"},
    {"name": "Darvishaliyeva Ziyoda", "subject": "Matematika"},
    {"name": "To`ramirzayeva Mardona", "subject": "Matematika"},
    {"name": "Rahimov Ilyos", "subject": "Matematika"},
    {"name": "Luxmonova Munisxon", "subject": "Informatika"},
    {"name": "Hasanov Dilshod", "subject": "Informatika"},
    {"name": "Soliyeva Nigora", "subject": "Informatika"},
    {"name": "Mamadiyev G'anijon", "subject": "Fizika"},
    {"name": "Salomov Zoirbek", "subject": "Fizika"},
    {"name": "Musayeva Dilafruz", "subject": "Kimyo"},
     {"name": "Raximov Abrorbek", "subject": "Kimyo"},
    {"name": "Mamatova Gulnoza", "subject": "Biologiya"},
    {"name": "Jabbarov Azimjon", "subject": "Biologiya"},
    {"name": "Umarova Munira", "subject": "Biologiya"},
    {"name": "To`ychiyev Murodilla", "subject": "Geografiya"},
    {"name": "Darvishova Nasiba", "subject": "Geografiya"},
    {"name": "Usmonova Gulhayo", "subject": "Geografiya"},
    {"name": "Nizomov Doniyor", "subject": "Iqtisod"},
    {"name": "Jo`raboyev Hasanboy", "subject": "Jismoniy tarbiya"},
    {"name": "Ashirmatov Bobur", "subject": "Jismoniy tarbiya"},
    {"name": "Yusupov Kozimjon", "subject": "Jismoniy tarbiya"},
    {"name": "Omonaliyev Jaloldin", "subject": "Jismoniy tarbiya"},
    {"name": "Xo'jayeva Sayyora", "subject": "Jismoniy tarbiya"},
    {"name": "Mirzahmedova Fotima", "subject": "Jismoniy tarbiya"},
    {"name": "Karimova Dilnoza", "subject": "Musiqa"},
    {"name": "Yoqubjonova Nazokat", "subject": "Musiqa"},
    {"name": "Nabijonov Azizbek", "subject": "Musiqa"},
    {"name": "Jo`rayeva Zeboxon", "subject": "Texnologiya"},
    {"name": "Jamoliddinov Shavkatjon", "subject": "Texnologiya"},
    {"name": "Abdurahimova Kamola", "subject": "Texnologiya"},
    {"name": "Ibragimova Dilorom", "subject": "Texnologiya"},
    {"name": "Yo`ldasheva Muazzam", "subject": "Tasviriy sa'nat"},
    {"name": "Mamatova Nilufar", "subject": "Boshlang`ich ta`lim"},
    {"name": "Sodikova Gulbahor", "subject": "Boshlang`ich ta`lim"},
    {"name": "Sarbarova Malika", "subject": "Boshlang`ich ta`lim"},
    {"name": "Xakimova Malohat", "subject": "Boshlang`ich ta`lim"},
    {"name": "O`rinboyeva Muhayyo", "subject": "Boshlang`ich ta`lim"},
    {"name": "Nishonova Sayyora", "subject": "Boshlang`ich ta`lim"},
    {"name": "To`xtanazarova Dilobar", "subject": "Boshlang`ich ta`lim"},
    {"name": "Saidova Laylixon", "subject": "Boshlang`ich ta`lim"},
    {"name": "Yusupova Matluba", "subject": "Boshlang`ich ta`lim"},
    {"name": "Ummataliyeva Komila", "subject": "Boshlang`ich ta`lim"},
    {"name": "Turdaliyeva Matluba", "subject": "Boshlang`ich ta`lim"},
    {"name": "Kodirova Dilorom", "subject": "Boshlang`ich ta`lim"},
    {"name": "Jo`raboyeva Mohigul", "subject": "Boshlang`ich ta`lim"},
    {"name": "Mirzaraxmatova Muhabbat", "subject": "Boshlang`ich ta`lim"},
    {"name": "Azamjonova Sarvinoz", "subject": "Boshlang`ich ta`lim"},
    {"name": "Ahmadaliyeva Onorxon", "subject": "Boshlang`ich ta`lim"},
    {"name": "Mirabdullayeva Xurshida", "subject": "Boshlang`ich ta`lim"},
    {"name": "Yarasheva Gulnora", "subject": "Boshlang`ich ta`lim"},
    {"name": "Ikromov Azizbek", "subject": "Boshlang`ich ta`lim"},
    {"name": "Rahmonchayeva O`lmasxon", "subject": "Boshlang`ich ta`lim"},
    {"name": "Isomiddinova Sarvinoz", "subject": "Boshlang`ich ta`lim"},
    {"name": "Boltaboyeva Muribat", "subject": "Boshlang`ich ta`lim"},
]


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id INTEGER PRIMARY KEY,
            full_name TEXT,
            subject TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            teacher_name TEXT,
            class_name TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS club_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            teacher_name TEXT,
            subject TEXT,
            student_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


class ReportState(StatesGroup):
  registering = State()
  choosing_class = State()
  choosing_hw_status = State()
  waiting_hw_media = State()
  waiting_club_count = State()
  waiting_club_media = State()


bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def get_registered_teacher(teacher_id):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT full_name, subject FROM teachers WHERE teacher_id = ?",
      (teacher_id,),
  )
  res = cursor.fetchone()
  conn.close()
  return res


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
  await state.clear()
  teacher = get_registered_teacher(message.from_user.id)

  if not teacher:
    await message.answer(
        "👋 Assalomu alaykum! Maktab nazorat botiga xush kelibsiz.\n\n"
        "Tizimga kirish uchun rasmiy ro'yxatdagi **Ism va Familiyangizni** to'liq"
        " yozib yuboring (Masalan: *Qo'chqarov Akram*):"
    )
    await state.set_state(ReportState.registering)
    return

  await show_main_menu(message, teacher[0], teacher[1])


async def show_main_menu(message: types.Message, name: str, subject: str):
  buttons = [
      [
          InlineKeyboardButton(
              text="📚 Uyga vazifa (Sinf rahbari)", callback_data="menu_hw"
          )
      ],
      [
          InlineKeyboardButton(
              text="🏆 To'garak hisoboti (Fan o'qituvchisi)",
              callback_data="menu_club",
          )
      ],
  ]

  if message.from_user.id in ADMIN_IDS:
    buttons.append([
        InlineKeyboardButton(
            text="📊 Excel Hisobotlar (Rahbariyat)", callback_data="get_excel"
        )
    ])

  keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
  await message.answer(
      f"Xush kelibsiz, **{name}**!\nMutaxassislik: *{subject}*\n\nKerakli bo'limni"
      " tanlang:",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )


# --- RO'YXATDAN O'TISH ---
@dp.message(ReportState.registering, F.text)
async def process_registration(message: types.Message, state: FSMContext):
  user_input = message.text.strip().lower()

  matched_teacher = None
  for t in OFFICIAL_TEACHERS:
    if t["name"].lower() == user_input:
      matched_teacher = t
      break

  if not matched_teacher:
    await message.answer(
        "❌ Kechirasiz, bu ism maktabimizning rasmiy o'qituvchilar ro'yxatida"
        " topilmadi.\nIltimos, Ism va Familiyangizni to'g'ri va to'liq yozing:"
    )
    return

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO teachers (teacher_id, full_name, subject) VALUES"
      " (?, ?, ?)",
      (message.from_user.id, matched_teacher["name"], matched_teacher["subject"]),
  )
  conn.commit()
  conn.close()

  await state.clear()
  await message.answer(
      f"✅ Profilingiz biriktirildi: **{matched_teacher['name']}**"
      f" ({matched_teacher['subject']})",
      parse_mode="Markdown",
  )
  await show_main_menu(message, matched_teacher["name"], matched_teacher["subject"])


# --- 1. UYGA VAZIFA HISOBOTI (SINFLAR RO'YXATI) ---
@dp.callback_query(F.data == "menu_hw")
async def choose_class(callback: types.CallbackQuery, state: FSMContext):
  keyboard_buttons = []
  for i in range(0, len(CLASSES_LIST), 3):
    row = [
        InlineKeyboardButton(
            text=CLASSES_LIST[i], callback_data=f"class_{CLASSES_LIST[i]}"
        )
    ]
    if i + 1 < len(CLASSES_LIST):
      row.append(
          InlineKeyboardButton(
              text=CLASSES_LIST[i + 1],
              callback_data=f"class_{CLASSES_LIST[i+1]}",
          )
      )
    if i + 2 < len(CLASSES_LIST):
      row.append(
          InlineKeyboardButton(
              text=CLASSES_LIST[i + 2],
              callback_data=f"class_{CLASSES_LIST[i+2]}",
          )
      )
    keyboard_buttons.append(row)

  keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
  await callback.message.edit_text(
      "📋 O'zingiz biriktirilgan sinfni tanlang:", reply_markup=keyboard
  )
  await state.set_state(ReportState.choosing_class)


@dp.callback_query(ReportState.choosing_class, F.data.startswith("class_"))
async def process_class_selection(
    callback: types.CallbackQuery, state: FSMContext
):
  selected_class = callback.data.split("_")[1]
  await state.update_data(selected_class=selected_class)

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="✅ Bajardi", callback_data="status_Bajardi")],
          [
              InlineKeyboardButton(
                  text="❌ Bajarmadi", callback_data="status_Bajarmadi"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⚠️ Chala bajardi", callback_data="status_Chala"
              )
          ],
      ]
  )
  await callback.message.edit_text(
      f"Sinf: **{selected_class}**\nUyga vazifa holatini tanlang:",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await state.set_state(ReportState.choosing_hw_status)


@dp.callback_query(
    ReportState.choosing_hw_status, F.data.startswith("status_")
)
async def process_hw_status(callback: types.CallbackQuery, state: FSMContext):
  status = callback.data.split("_")[1]
  data = await state.get_data()
  selected_class = data.get("selected_class")
  teacher = get_registered_teacher(callback.from_user.id)

  if status == "Bajarmadi":
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO homework_reports (teacher_id, teacher_name, class_name,"
        " status) VALUES (?, ?, ?, ?)",
        (callback.from_user.id, teacher[0], selected_class, "Bajarmadi"),
    )
    conn.commit()
    conn.close()

    await state.clear()
    await callback.message.edit_text(
        f"✅ **{selected_class}** sinfi uchun 'Bajarmadi' holati saqlandi!"
    )
  else:
    await state.update_data(status=status)
    await callback.message.edit_text(
        f"📸 **{selected_class}** sinfining uyga vazifasi isboti uchun **rasm"
        " yoki video** yuboring:",
        parse_mode="Markdown",
    )
    await state.set_state(ReportState.waiting_hw_media)


@dp.message(ReportState.waiting_hw_media, F.photo | F.video)
async def process_hw_media(message: types.Message, state: FSMContext):
  data = await state.get_data()
  selected_class = data.get("selected_class")
  status = data.get("status")
  teacher = get_registered_teacher(message.from_user.id)

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO homework_reports (teacher_id, teacher_name, class_name,"
      " status) VALUES (?, ?, ?, ?)",
      (message.from_user.id, teacher[0], selected_class, status),
  )
  conn.commit()
  conn.close()

  await state.clear()
  await message.answer(
      f"✅ **{selected_class}** sinfining hisoboti rasm/video bilan birga"
      " saqlandi!",
      parse_mode="Markdown",
  )


# --- 2. TO'GARAK HISOBOTI ---
@dp.callback_query(F.data == "menu_club")
async def start_club_report(callback: types.CallbackQuery, state: FSMContext):
  teacher = get_registered_teacher(callback.from_user.id)
  await callback.message.edit_text(
      f"🏆 Fani: **{teacher[1]}**\n\nBugungi to'garak mashg'ulotida **nechta"
      " o'quvchi** qatnashdi? (Faqat raqam kiriting, masalan: 12):",
      parse_mode="Markdown",
  )
  await state.set_state(ReportState.waiting_club_count)


@dp.message(ReportState.waiting_club_count, F.text)
async def process_club_count(message: types.Message, state: FSMContext):
  if not message.text.isdigit():
    await message.answer("❌ Iltimos, faqat raqam kiriting (masalan: 15):")
    return

  await state.update_data(student_count=int(message.text))
  await message.answer(
      "📸 Mashg'ulot jarayonidan isbot tariqasida **rasm yoki video** yuboring:",
      parse_mode="Markdown",
  )
  await state.set_state(ReportState.waiting_club_media)


@dp.message(ReportState.waiting_club_media, F.photo | F.video)
async def process_club_media(message: types.Message, state: FSMContext):
  data = await state.get_data()
  student_count = data.get("student_count")
  teacher = get_registered_teacher(message.from_user.id)

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO club_reports (teacher_id, teacher_name, subject,"
      " student_count) VALUES (?, ?, ?, ?)",
      (message.from_user.id, teacher[0], teacher[1], student_count),
  )
  conn.commit()
  conn.close()

  await state.clear()
  await message.answer(
      f"✅ **{teacher[1]}** to'garagi bo'yicha **{student_count} nafar**"
      " o'quvchi qatnashgani rasm/video bilan saqlandi!",
      parse_mode="Markdown",
  )


# --- 3. EXCEL HISOBOT GENERATSIYASI (2 TA LIST) ---
@dp.callback_query(F.data == "get_excel")
async def generate_excel_report(callback: types.CallbackQuery):
  if callback.from_user.id not in ADMIN_IDS:
    await callback.answer(
        "❌ Kechirasiz, bu funksiya faqat rahbarlar uchun!", show_alert=True
    )
    return

  wb = openpyxl.Workbook()

  now = datetime.now()
  week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
  month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # 1-SAHIFA: UYGA VAZIFA (SINFLAR BO'YICHA)
  ws1 = wb.active
  ws1.title = "Uyga Vazifa (Sinflar)"
  ws1.append([
      "T/R",
      "Sinf",
      "Mas'ul O'qituvchi",
      "Haftalik yuborilgan (Soni)",
      "Oylik yuborilgan (Soni)",
      "Oxirgi Yuborilgan Vaqt",
      "Oxirgi Holat",
  ])

  cursor.execute(
      "SELECT class_name, teacher_name, status, timestamp FROM"
      " homework_reports ORDER BY timestamp DESC"
  )
  hw_rows = cursor.fetchall()

  # Statistikani hisoblash
  stats_hw = {}
  for r in hw_rows:
    c_name, t_name, status, ts = r[0], r[1], r[2], r[3]
    if c_name not in stats_hw:
      stats_hw[c_name] = {
          "teacher": t_name,
          "week_cnt": 0,
          "month_cnt": 0,
          "last_time": ts,
          "last_status": status,
      }

    if ts >= week_ago:
      stats_hw[c_name]["week_cnt"] += 1
    if ts >= month_ago:
      stats_hw[c_name]["month_cnt"] += 1

  idx = 1
  for c_name, data in stats_hw.items():
    ws1.append([
        idx,
        c_name,
        data["teacher"],
        data["week_cnt"],
        data["month_cnt"],
        data["last_time"],
        data["last_status"],
    ])
    idx += 1

  # 2-SAHIFA: TO'GARAK MASHG'ULOTLARI
  ws2 = wb.create_sheet(title="To'garaklar Hisoboti")
  ws2.append([
      "T/R",
      "To'garak / Fan Nomi",
      "O'qituvchi F.I.O.",
      "Haftalik O'tkazilgan (Soni)",
      "Oylik O'tkazilgan (Soni)",
      "Oxirgi Qatnashgan O'quvchilar Soni",
      "Oxirgi Vaqt",
  ])

  cursor.execute(
      "SELECT subject, teacher_name, student_count, timestamp FROM club_reports"
      " ORDER BY timestamp DESC"
  )
  club_rows = cursor.fetchall()

  stats_club = {}
  for r in club_rows:
    subj, t_name, count, ts = r[0], r[1], r[2], r[3]
    if subj not in stats_club:
      stats_club[subj] = {
          "teacher": t_name,
          "week_cnt": 0,
          "month_cnt": 0,
          "last_count": count,
          "last_time": ts,
      }

    if ts >= week_ago:
      stats_club[subj]["week_cnt"] += 1
    if ts >= month_ago:
      stats_club[subj]["month_cnt"] += 1

  idx = 1
  for subj, data in stats_club.items():
    ws2.append([
        idx,
        subj,
        data["teacher"],
        data["week_cnt"],
        data["month_cnt"],
        data["last_count"],
        data["last_time"],
    ])
    idx += 1

  # 3-SAHIFA: HALI RO'YXATDAN O'TMAGANLAR
  ws3 = wb.create_sheet(title="Ro'yxatdan O'tmaganlar")
  ws3.append(["T/R", "O'qituvchi F.I.O.", "Fani", "Holati"])

  cursor.execute("SELECT full_name FROM teachers")
  reg_names = {row[0] for row in cursor.fetchall()}
  conn.close()

  idx = 1
  for t in OFFICIAL_TEACHERS:
    if t["name"] not in reg_names:
      ws3.append([idx, t["name"], t["subject"], "Botga kirmagan"])
      idx += 1

  file_path = "Maktab_Nazorat_Hisoboti.xlsx"
  wb.save(file_path)

  if os.path.exists(file_path):
    doc = BufferedInputFile(open(file_path, "rb").read(), filename=file_path)
    await callback.message.answer_document(
        doc,
        caption=(
            "📊 **Maktab bo'yicha to'liq hisobot va statistikalar"
            " tayyor!**\n\n- 1-List: Sinflar uyga vazifasi\n- 2-List: To'garaklar"
            " qatnashuvi\n- 3-List: Ro'yxatdan o'tmaganlar"
        ),
        parse_mode="Markdown",
    )
    os.remove(file_path)


async def main():
  init_db()
  logging.basicConfig(level=logging.INFO)
  print("Sinf va to'garak nazorati boti ishga tushdi...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())