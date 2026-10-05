import sys
import asyncio
from datetime import datetime, date, timedelta
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8611800895:AAGG5X2MNsHjk_31IDTGixDWZDt_MCw_ZDA"
USER_ID = 5639929575
CITY = "Пермь"
TIMEZONE = "Asia/Yekaterinburg"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

WEEKDAYS_RU = [
    "понедельник", "вторник", "среда",
    "четверг", "пятница", "суббота", "воскресенье"
]

MONTHS_RU = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]

WMO_CODES = {
    0: "ясно ☀️", 1: "в основном ясно 🌤", 2: "переменная облачность ⛅",
    3: "пасмурно ☁️", 45: "туман 🌫", 48: "изморозь 🌫", 51: "легкая морось 🌧",
    53: "морось 🌧", 55: "плотная морось 🌧", 61: "небольшой дождь 🌧",
    63: "умеренный дождь 🌧", 65: "сильный дождь 🌧", 71: "небольшой снег 🌨",
    73: "снегопад 🌨", 75: "сильный снегопад ❄️", 77: "снежная крупа ❄️",
    80: "ливневый дождь 🌧", 81: "сильный ливень 🌧", 82: "шквальный ливень ⛈",
    85: "ливневый снег 🌨", 86: "сильный снегопад ❄️", 95: "гроза ⚡"
}

SEMESTER_START = date(2026, 9, 1)

def get_week_type(target_date: date) -> int:
    start_monday = SEMESTER_START - timedelta(days=SEMESTER_START.weekday())
    diff_weeks = (target_date - start_monday).days // 7
    return 1 if (diff_weeks % 2 == 0) else 2

SCHEDULE_MAP = {
    0: {
        1: [("08:00", "Иностранный язык (пр) ауд. 408/114 к.А"), ("09:40", "Прикладная физкультура (пр)")],
        2: [("08:00", "Иностранный язык (пр) ауд. 408/114 к.А"), ("09:40", "Прикладная физкультура (пр)")]
    },
    1: {
        1: [
            ("09:40", "Введение в инженерную деятельность (пр) ауд. 229 к.А"),
            ("11:30", "Математика (лек) ауд. 5б к.Д"),
            ("13:20", "Физическая культура и спорт (лек) ауд. 6б к.Д")
        ],
        2: [
            ("09:40", "Введение в инженерную деятельность (пр) ауд. 229 к.А"),
            ("11:30", "Математика (лек) ауд. 5б к.Д"),
            ("13:20", "Физическая культура и спорт (лек) ауд. 6б к.Д")
        ]
    },
    2: {
        1: [
            ("13:20", "Основы российской государственности (лек) ауд. 6б к.Д"),
            ("15:00", "История России (лек) ауд. 6б к.Д"),
            ("16:40", "Основы российской государственности (пр) ауд. 6б к.Д")
        ],
        2: [
            ("11:30", "Дискретная математика и мат. логика (пр) ауд. 406 к.А"),
            ("13:20", "История России (пр) ауд. 6б к.Д")
        ]
    },
    3: {
        1: [
            ("09:40", "Математика (пр) ауд. 104 к.В"),
            ("11:30", "Математика (пр) ауд. 104 к.В"),
            ("13:20", "Учебно-исследовательская работа (пр) ауд. 127 к.А")
        ],
        2: [
            ("09:40", "Учебно-исследовательская работа (лек) ауд. 416 к.А"),
            ("11:30", "Информатика (лек) ауд. 5б к.Д"),
            ("13:20", "Основы алгоритмизации и программирования (лек) ауд. 5б к.Д"),
            ("15:00", "Введение в инженерную деятельность (лек) ауд. 5б к.Д")
        ]
    },
    4: {
        1: [
            ("09:40", "Прикладная физкультура (пр)"),
            ("11:30", "Дискретная математика и мат. логика (лек) ауд. 402 к.А"),
            ("13:20", "Основы алгоритмизации и программирования (лаб) ауд. 409 к.А"),
            ("15:00", "Информатика (лаб) ауд. 409 к.А")
        ],
        2: [
            ("09:40", "Прикладная физкультура (пр)"),
            ("11:30", "Дискретная математика и мат. логика (лек) ауд. 402 к.А"),
            ("13:20", "Основы алгоритмизации и программирования (лаб) ауд. 409 к.А"),
            ("15:00", "Информатика (лаб) ауд. 409 к.А")
        ]
    },
    5: {1: [], 2: []},
    6: {1: [], 2: []}
}

# --- РАСПИСАНИЕ РЕЙСОВ АВТОБУСОВ ПО ЧАСАМ ---
# Сетка рейсов (будни). Если нужно скорректировать под конкретную остановку,
# достаточно изменить минуты в этом словаре.
BUS_SCHEDULE = {
    "20": [
        "06:32", "06:44", "06:56",
        "07:07", "07:18", "07:29", "07:40", "07:51",
        "08:02", "08:14", "08:26", "08:38", "08:50",
        "09:02", "09:15", "09:30", "09:45",
        "10:00", "10:15", "10:30", "10:45",
        "11:00", "11:15", "11:30", "11:45", "11:58",
        "12:12", "12:26", "12:40", "12:54"
    ],
    "2": [
        "06:35", "06:50",
        "07:05", "07:20", "07:35", "07:50",
        "08:05", "08:20", "08:35", "08:50",
        "09:08", "09:26", "09:44",
        "10:02", "10:20", "10:38", "10:56",
        "11:14", "11:32", "11:50",
        "12:08", "12:26", "12:44"
    ]
}


def get_exact_buses_and_wakeup(first_lesson_time_str: str | None):
    """Находит конкретные рейсы в интервале 70-90 минут до первой пары."""
    if not first_lesson_time_str:
        return "Сегодня автобус не нужен.", "⏰ Будильник можно не ставить — выходной!"

    lesson_dt = datetime.strptime(first_lesson_time_str, "%H:%M")
    window_start = lesson_dt - timedelta(minutes=90)
    window_end = lesson_dt - timedelta(minutes=70)

    matched_buses = []
    for route, departures in BUS_SCHEDULE.items():
        for dep_str in departures:
            dep_dt = datetime.strptime(dep_str, "%H:%M")
            if window_start <= dep_dt <= window_end:
                diff_min = int((lesson_dt - dep_dt).total_seconds() // 60)
                matched_buses.append((dep_dt, f"Автобус <b>№{route}</b> в <b>{dep_str}</b> (за {diff_min} мин до пары)"))

    # Сортируем рейсы по времени отправления
    matched_buses.sort(key=lambda x: x[0])

    if matched_buses:
        first_bus_dt = matched_buses[0][0]
        # Будильник ставим за 40 минут до первого подходящего автобуса
        wakeup_dt = first_bus_dt - timedelta(minutes=40)
        wakeup_str = wakeup_dt.strftime("%H:%M")
        first_bus_str = first_bus_dt.strftime("%H:%M")

        bus_lines = "\n".join([f"  • {item[1]}" for item in matched_buses])
        bus_text = f"Подходящие рейсы (окно {window_start.strftime('%H:%M')}–{window_end.strftime('%H:%M')}):\n{bus_lines}"
        wakeup_text = f"⏰ <b>Будильник на: {wakeup_str}</b> (за 40 мин до рейса в {first_bus_str})"
    else:
        # Если в узкое окно рейс не попал, берем ближайший до начала пары
        bus_text = f"Окно выезда: <b>{window_start.strftime('%H:%M')} — {window_end.strftime('%H:%M')}</b> (проверь онлайн-табло)."
        wakeup_text = f"⏰ <b>Будильник на: {(window_start - timedelta(minutes=40)).strftime('%H:%M')}</b>"

    return bus_text, wakeup_text


async def get_weather_forecast(city: str) -> tuple[str, str]:
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude=58.0105&longitude=56.2502&"
        "hourly=temperature_2m,precipitation,weathercode&"
        "timezone=Asia%2FYekaterinburg&forecast_days=1"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status != 200:
                    return "Не удалось связаться с погодным сервисом.", "Ориентируйся по погоде за окном."

                data = await response.json()
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                codes = hourly.get("weathercode", [])
                precips = hourly.get("precipitation", [])

                def get_hour_data(target_h: int) -> tuple[int, str]:
                    idx = min(target_h, len(times) - 1)
                    t = round(temps[idx])
                    desc = WMO_CODES.get(codes[idx], "облачно")
                    return t, desc

                m_temp, m_desc = get_hour_data(8)
                d_temp, d_desc = get_hour_data(14)
                e_temp, e_desc = get_hour_data(20)

                weather_block = (
                    f"  • Утро (08:00): {m_temp:+d}°C, {m_desc}\n"
                    f"  • День (14:00): {d_temp:+d}°C, {d_desc}\n"
                    f"  • Вечер (20:00): {e_temp:+d}°C, {e_desc}"
                )

                min_t = min(temps) if temps else m_temp
                max_t = max(temps) if temps else d_temp
                has_precip = any(p > 0.1 for p in precips)

                if max_t < -10:
                    outfit = "Очень морозно: зимний пуховик, теплая шапка, шарф и перчатки."
                elif max_t < 0:
                    outfit = "Зимняя куртка, шапка, плотные штаны/джинсы."
                elif min_t < 4 and max_t >= 10:
                    outfit = "Заметный перепад: утром холодно (надень теплую кофту под куртку), днем будет комфортно."
                elif 0 <= max_t < 10:
                    outfit = "Демисезонная куртка или плотная ветровка со свитером/худи, шапка."
                elif 10 <= max_t < 18:
                    outfit = "Легкая куртка, бомбер или плотная толстовка."
                else:
                    outfit = "Тепло: футболка, рубашка или лонгслив."

                if has_precip:
                    outfit += " ⚠️ Ожидаются осадки — не забудь зонт!"

                return weather_block, outfit

    except Exception:
        return "Ошибка сети при запросе погоды.", "Оденься по сезону."


async def build_morning_message() -> str:
    now = datetime.now()
    target_date = now.date()
    weekday_idx = target_date.weekday()
    week_type = get_week_type(target_date)
    week_label = "1-я неделя (числитель)" if week_type == 1 else "2-я неделя (знаменатель)"

    day = target_date.day
    month = MONTHS_RU[target_date.month]
    weekday_name = WEEKDAYS_RU[weekday_idx]

    today_lessons = SCHEDULE_MAP.get(weekday_idx, {}).get(week_type, [])

    if today_lessons:
        lessons_text = "\n".join([f"  • <b>{t}</b> — {subj}" for t, subj in today_lessons])
        first_time = today_lessons[0][0]
        bus_info, _ = get_exact_buses_and_wakeup(first_time)
    else:
        lessons_text = "  • Пар нет (выходной) 🎉"
        bus_info = "Сегодня никуда ехать не нужно."

    extra = ""
    if weekday_idx == 4:
        extra = "\n\n🚗 <b>Вечерний план:</b>\n  • <b>18:30</b> — Автошкола"

    weather_info, clothing_advice = await get_weather_forecast(CITY)

    return (
        f"☀️ <b>Доброе утро, Никита!</b>\n"
        f"📅 Сегодня <b>{day} {month}</b>, <b>{weekday_name}</b> ({week_label})\n\n"
        f"📚 <b>Расписание пар на сегодня:</b>\n{lessons_text}"
        f"{extra}\n\n"
        f"🚌 <b>Автобусы к первой паре на {today_lessons[0][0] if today_lessons else '-'}:</b>\n{bus_info}\n\n"
        f"🌤 <b>Погода на сегодня ({CITY}):</b>\n{weather_info}\n\n"
        f"🧥 <b>Что надеть:</b> {clothing_advice}"
    )


async def build_night_message() -> str:
    tomorrow = datetime.now().date() + timedelta(days=1)
    weekday_idx = tomorrow.weekday()
    week_type = get_week_type(tomorrow)
    week_label = "1-я неделя" if week_type == 1 else "2-я неделя"

    day = tomorrow.day
    month = MONTHS_RU[tomorrow.month]
    weekday_name = WEEKDAYS_RU[weekday_idx]

    tomorrow_lessons = SCHEDULE_MAP.get(weekday_idx, {}).get(week_type, [])

    if tomorrow_lessons:
        lessons_text = "\n".join([f"  • <b>{t}</b> — {subj}" for t, subj in tomorrow_lessons])
        first_time = tomorrow_lessons[0][0]
        bus_info, wakeup_info = get_exact_buses_and_wakeup(first_time)
    else:
        lessons_text = "  • Пар нет (выходной) 🎉"
        bus_info = "Завтра автобус не нужен."
        wakeup_info = "⏰ Будильник можно не ставить — завтра законный отдых!"

    extra = ""
    if weekday_idx == 4:
        extra = "\n\n🚗 <b>Напоминание:</b> завтра пятница, в 18:30 автошкола!"

    return (
        f"🌙 <b>Добрый вечер, Никита! План на завтра ({day} {month}, {weekday_name}):</b>\n"
        f"<i>Неделя: {week_label}</i>\n\n"
        f"📚 <b>Расписание пар:</b>\n{lessons_text}"
        f"{extra}\n\n"
        f"🚌 <b>Рейсы автобуса (№20 / №2):</b>\n{bus_info}\n\n"
        f"{wakeup_info}\n\n"
        f"Спокойной ночи и приятного отдыха! 😴"
    )


async def send_morning_message():
    text = await build_morning_message()
    await bot.send_message(chat_id=USER_ID, text=text, parse_mode="HTML")


async def send_night_message():
    text = await build_night_message()
    await bot.send_message(chat_id=USER_ID, text=text, parse_mode="HTML")


@dp.message(Command("morning"))
async def cmd_morning(message: Message):
    text = await build_morning_message()
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("night"))
async def cmd_night(message: Message):
    text = await build_night_message()
    await message.answer(text, parse_mode="HTML")


async def main():
    scheduler.add_job(
        send_morning_message,
        trigger=CronTrigger(hour=7, minute=0, timezone=TIMEZONE)
    )
    scheduler.add_job(
        send_night_message,
        trigger=CronTrigger(hour=23, minute=0, timezone=TIMEZONE)
    )
    scheduler.start()
    print("Бот запущен. Расписание: 07:00 и 23:00 (Пермь).")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())