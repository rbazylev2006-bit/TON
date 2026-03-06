import asyncio
import logging
import os
from datetime import datetime
import io

import aiohttp
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from aiogram import Bot, types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
HISTORY_DAYS = 1

logging.basicConfig(level=logging.INFO)

async def get_ton_history(days=7):
    url = "https://api.coingecko.com/api/v3/coins/the-open-network/market_chart"
    params = {"vs_currency": "usd", "days": days}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            timestamps = [p[0] for p in data['prices']]
            prices = [p[1] for p in data['prices']]
            dates = [datetime.fromtimestamp(ts/1000) for ts in timestamps]
            return dates, prices

async def get_current_ton_usd():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data["the-open-network"]["usd"]

async def get_usd_rub():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data["rates"]["RUB"]

def generate_chart(dates, prices, ton_usd, ton_rub):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dates, prices, color='#00a3ff', linewidth=2, marker='o', markersize=4)
    ax.fill_between(dates, prices, alpha=0.2, color='#00a3ff')
    ax.set_facecolor('#1c1c1c')
    fig.patch.set_facecolor('#1c1c1c')
    ax.grid(True, linestyle='--', alpha=0.5, color='gray')
    ax.set_xlabel('Дата', color='white')
    ax.set_ylabel('Цена TON (USD)', color='white')
    ax.tick_params(colors='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.xticks(rotation=45)
    title = f'TON / USD: ${ton_usd:.2f}  |  TON / RUB: {ton_rub:.2f} ₽'
    ax.set_title(title, color='white', fontsize=14, pad=20)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    return buf

async def main():
    logging.info("Запуск задачи...")
    bot = Bot(token=BOT_TOKEN)
    try:
        dates, prices = await get_ton_history(HISTORY_DAYS)
        ton_usd = await get_current_ton_usd()
        usd_rub = await get_usd_rub()
        ton_rub = ton_usd * usd_rub
        chart_buf = generate_chart(dates, prices, ton_usd, ton_rub)
        caption = (
            f"📊 График курса TON\n"
            f"💰 Текущий курс: ${ton_usd:.2f} / {ton_rub:.2f} ₽\n"
            f"🕐 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"#TON #криптовалюта"
        )
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=types.BufferedInputFile(chart_buf.getvalue(), filename="ton_chart.png"),
            caption=caption
        )
        logging.info("Пост отправлен")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
