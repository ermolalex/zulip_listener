import asyncio

from maxapi import Bot
from maxapi.types import InputMedia
from config import settings

import helpers

bot = Bot(token=settings.MAX_TOKEN)


# @helpers.async_exec
def main():
    # Вариант 1: отправка напрямую через InputMedia
    text = "None"
    attach = [InputMedia(path="logo.png"),]

    asyncio.run(
        bot.send_message(
            user_id=184560163,
            text=text,
            attachments=attach,
        )
    )

    asyncio.run(
        bot.close_session()
    )

    # # Вариант 2: ручная загрузка + отправка attachment. (Подходит для рассылок)
    # media = InputMedia("logo.png")
    # attachment = await bot.upload_media(media)
    # await bot.send_message(
    #     chat_id=...,
    #     attachments=[attachment],
    # )


if __name__ == "__main__":
    main()