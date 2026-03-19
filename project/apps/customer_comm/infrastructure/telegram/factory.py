from .client import TelegramBotProvider


def get_telegram_provider() -> TelegramBotProvider:
    return TelegramBotProvider()
