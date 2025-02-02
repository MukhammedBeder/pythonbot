
import telebot
import requests

# Токен бота
API_TOKEN = '7586259594:AAH3WL9JBWwpocXR_0s3P5dPIE5Yc38TZmQ'
ANTIPLAGIAT_API_KEY = '12025e688e01b9b32359f66fd9db1aed'

# Создаем экземпляр бота
bot = telebot.TeleBot(API_TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне текст, и я проверю его на уникальность.")

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def check_plagiarism(message):
    text = message.text

    # Отправляем текст на проверку (пример для Text.ru API)
    response = requests.post(
        'https://api.text.ru/post',
        data={
            'text': text,
            'userkey': ANTIPLAGIAT_API_KEY,
            'visible': 'vis_on'  # Показывать источники заимствований
        }
    )

    if response.status_code == 200:
        result = response.json()
        if 'text_uid' in result:
            # Получаем результат проверки
            uid = result['text_uid']
            bot.reply_to(message, f"Текст принят на проверку. ID проверки: {uid}. Подожди немного...")

            # Ждем и запрашиваем результат
            import time
            time.sleep(20)  # Ждем 10 секунд (зависит от сервиса)
            result_response = requests.post(
                'https://api.text.ru/post',
                data={
                    'uid': uid,
                    'userkey': ANTIPLAGIAT_API_KEY
                }
            )

            if result_response.status_code == 200:
                result_data = result_response.json()
                if 'text_unique' in result_data:
                    unique_percent = result_data['text_unique']
                    bot.reply_to(message, f"Уникальность текста: {unique_percent}%")
                else:
                    bot.reply_to(message, "Ошибка при получении результата.")
            else:
                bot.reply_to(message, "Ошибка при запросе результата.")
        else:
            bot.reply_to(message, "Ошибка при отправке текста на проверку.")
    else:
        bot.reply_to(message, "Ошибка подключения к сервису антиплагиата.")

# Запуск бота
bot.polling()