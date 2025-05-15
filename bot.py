import asyncio
import aiohttp
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

API_TOKEN = '7736087566:AAHqxednEIYyABQ5P_Xba_3fVbmYBtX6erQ'
CHAT_ID = 455634817
CHECK_INTERVAL = 60  # сек; проверять каждые 5 минут

# Создаём бота с HTML-парсингом
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Множество уже отправленных ивентов
known_events: set[str] = set()

async def fetch_events() -> list[tuple[str, str]]:
    """
    Скачиваем главную страницу и возвращаем список кортежей (название, ссылка).
    """
    url = 'https://platform.cartelclash.io/'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
    soup = BeautifulSoup(html, 'html.parser')
    tiles = soup.find_all(class_='event-tile')
    result: list[tuple[str, str]] = []
    for tile in tiles:
        # заголовок внутри <h3>
        h3 = tile.find('h3')
        # ссылка — первая <a>
        a = tile.find('a', href=True)
        if h3 and a:
            title = h3.get_text(strip=True)
            link = a['href']
            # приводим ссылку к полному URL (если относительная)
            if link.startswith('/'):
                link = 'https://platform.cartelclash.io' + link
            result.append((title, link))
    return result

async def check_new_events():
    """
    Периодически проверяем страницу, сравниваем с known_events,
    и отправляем в чат новые.
    """
    global known_events
    while True:
        try:
            events = await fetch_events()
            for title, link in events:
                if title not in known_events:
                    known_events.add(title)
                    text = (
                        f"🆕 <b>Новый ивент</b>\n"
                        f"{title}\n"
                        f"<a href=\"{link}\">Перейти на сайт</a>"
                    )
                    await bot.send_message(CHAT_ID, text)
        except Exception as e:
            # просто выводим в консоль, чтобы бот не падал
            print("Ошибка при проверке ивентов:", e)
        await asyncio.sleep(CHECK_INTERVAL)

@dp.message(CommandStart())
async def on_start(message: types.Message):
    """
    При /start бот подтверждает, что запущен и начинает слушать ивенты.
    """
    await message.answer(
        "Бот запущен и будет уведомлять тебя о новых ивентах каждые 5 минут.\n"
        "Если что-то пойдёт не так — смотри логи в консоли."
    )

async def main():
    # старт параллельной задачи по проверке ивентов
    asyncio.create_task(check_new_events())
    # запускаем Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
