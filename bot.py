import os
import base64
import asyncio
from io import BytesIO

import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandStart


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_API_URL = os.getenv("MODEL_API_URL", "http://localhost:5000")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не найден в .env")


bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет. Отправь мне фото с яблоками, огурцами или помидорами, "
        "а я верну изображение с bbox и расчётами."
    )


async def send_image_to_model(image_bytes: bytes) -> dict:
    form = aiohttp.FormData()
    form.add_field(
        name="image",
        value=image_bytes,
        filename="image.jpg",
        content_type="image/jpeg"
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{MODEL_API_URL}/predict",
            data=form,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            data = await response.json()

            if response.status != 200:
                raise RuntimeError(data.get("error", "Ошибка обработки изображения"))

            return data


def make_caption(data: dict) -> str:
    counts = data["counts"]
    calculations = data["calculations"]

    return (
        "Результат анализа:\n\n"
        f"Яблоки: {counts['apple']} шт.\n"
        f"Огурцы: {counts['cucumber']} шт.\n"
        f"Помидоры: {counts['tomato']} шт.\n\n"
        "Расчёты:\n"
        f"Компот из яблок: {calculations['compote_liters']} л\n"
        f"Банки огурцов: {calculations['cucumber_jars']} банки\n"
        f"Банки помидоров: {calculations['tomato_jars']} банки\n\n"
        "Формулы:\n"
        "1 яблоко ≈ 0.15 л компота\n"
        "1 огурец ≈ 0.1 банки\n"
        "1 помидор ≈ 0.2 банки"
    )


@dp.message(F.photo)
async def handle_photo(message: Message):
    status_msg = await message.answer("Обрабатываю изображение...")

    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)

        image_buffer = BytesIO()
        await bot.download_file(file.file_path, image_buffer)

        image_bytes = image_buffer.getvalue()

        data = await send_image_to_model(image_bytes)

        result_image_bytes = base64.b64decode(data["image"])
        result_file = BufferedInputFile(
            result_image_bytes,
            filename="result.jpg"
        )

        await message.answer_photo(
            photo=result_file,
            caption=make_caption(data)
        )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"Ошибка: {e}")


@dp.message(F.document)
async def handle_document(message: Message):
    document = message.document

    if not document.mime_type or not document.mime_type.startswith("image/"):
        await message.answer("Отправь изображение файлом или обычным фото.")
        return

    status_msg = await message.answer("Обрабатываю изображение...")

    try:
        file = await bot.get_file(document.file_id)

        image_buffer = BytesIO()
        await bot.download_file(file.file_path, image_buffer)

        image_bytes = image_buffer.getvalue()

        data = await send_image_to_model(image_bytes)

        result_image_bytes = base64.b64decode(data["image"])
        result_file = BufferedInputFile(
            result_image_bytes,
            filename="result.jpg"
        )

        await message.answer_photo(
            photo=result_file,
            caption=make_caption(data)
        )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"Ошибка: {e}")


@dp.message()
async def fallback(message: Message):
    await message.answer("Отправь фото или изображение файлом.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())