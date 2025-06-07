# Telegram Finance Bot

## Файлы
- `main.py` — основной код бота
- `requirements.txt` — зависимости
- `env` — файл с токеном (впишите свой BOT_TOKEN)

## Как запустить:

1. Перейдите в папку:
   ```
   cd ~/Downloads/telegram_finance_bot_ready_v2
   ```

2. Откройте файл `env` и замените:
   ```
   BOT_TOKEN=your_bot_token_here
   ```
   на ваш токен, например:
   ```
   BOT_TOKEN=7712104265:AAF1HBJ8Mk1ypADd-r38jEZttqgXo-HrmOw
   ```

3. Установите зависимости:
   ```
   python3 -m pip install -r requirements.txt
   ```

4. Запустите бота:
   ```
   python3 main.py
   ```

5. В Telegram перейдите в чат с ботом, напишите `/start` и `/work`. Бот должен отвечать.

Если что-то не работает — проверьте правильность токена и установку зависимостей.
