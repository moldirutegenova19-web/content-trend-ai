import os
import asyncio
import logging

from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

from content_ai import research_content

load_dotenv(
    Path(__file__).with_name(".env"),
    override=True
)

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

keyboard = [
    ["💄 Сұлулық", "🏋️ Фитнес"],
    ["📚 Білім", "🍔 Тамақ"],
    ["✈️ Саяхат", "💼 Бизнес"],
    ["📱 Блогинг", "👗 Сән"],
    ["🔥 Трендтерді алу"],
    ["🔕 Жазылымнан бас тарту"]
]


async def start(update, context):
    await update.message.reply_text(
        "🚀 Trend Hunter AI агентіне қош келдіңіз!\n\n"
        "Мен сіздің жеке контент ассистентіңізбін.\n\n"
        "🔥 Өзекті трендтер\n"
        "💡 Контент идеялары\n"
        "🎬 Видео сценарийлері\n"
        "🎵 Музыка ұсыныстары\n"
        "#️⃣ Хэштегтер\n\n"
        "Өз бағытыңызды таңдаңыз немесе жазыңыз.\n"
        "Апталық есеп дүйсенбі күні 09:00-де келеді.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def send_report(bot, chat_id, niche):
    await bot.send_message(
        chat_id,
        "🔎 Контент трендтерін зерттеп жатырмын..."
    )

    try:
        result = await asyncio.to_thread(
            research_content, niche
        )

        for i in range(0, len(result), 3500):
            await bot.send_message(
                chat_id,
                result[i:i + 3500]
            )

    except Exception as error:
        logging.error(
            "Content error: %s, status: %s",
            type(error).__name__,
            getattr(error, "status_code", None)
        )

        await bot.send_message(
            chat_id,
            "⚠️ Есеп дайындау кезінде қате шықты. "
            "Кейінірек қайталап көріңіз."
        )


async def weekly_report(context):
    await send_report(
        context.bot,
        context.job.chat_id,
        context.job.data
    )


async def analyze(update, context):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "🔕 Жазылымнан бас тарту":
        for job in context.job_queue.get_jobs_by_name(
            str(chat_id)
        ):
            job.schedule_removal()

        await update.message.reply_text(
            "🔕 Апталық жазылым өшірілді."
        )
        return

    if text == "🔥 Трендтерді алу":
        niche = context.user_data.get("niche")

        if not niche:
            await update.message.reply_text(
                "Алдымен контент бағытын таңдаңыз."
            )
            return

        await send_report(
            context.bot, chat_id, niche
        )
        return

    niche = text
    context.user_data["niche"] = niche

    for job in context.job_queue.get_jobs_by_name(
        str(chat_id)
    ):
        job.schedule_removal()

    context.job_queue.run_daily(
        weekly_report,
        time=time(
            hour=9,
            minute=0,
            tzinfo=ZoneInfo("Asia/Almaty")
        ),
        days=(1,),
        chat_id=chat_id,
        data=niche,
        name=str(chat_id)
    )

    await update.message.reply_text(
        f"✅ Бағыт: {niche}\n\n"
        "📅 Апта сайын дүйсенбі\n"
        "⏰ 09:00 Алматы уақыты\n"
        "🔔 Жазылым қосылды!"
    )

    await send_report(
        context.bot, chat_id, niche
    )


def main():
    if not TOKEN:
        raise RuntimeError("Telegram токені табылмады")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            analyze
        )
    )

    print("Trend Hunter AI запущен!", flush=True)

    app.run_polling()


if __name__ == "__main__":
    main()