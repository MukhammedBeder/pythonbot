import os
import time
import json
import requests
import telebot
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

# Регистрация шрифтов
try:
    # Путь к шрифтам должен быть корректным, проверьте, что файлы шрифтов находятся в папке проекта
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
except Exception as e:
    print(f"Ошибка регистрации шрифтов: {e}")
    print("Шрифты DejaVu не найдены, используется стандартный шрифт Helvetica.")

API_TOKEN = '7586259594:AAH3WL9JBWwpocXR_0s3P5dPIE5Yc38TZmQ'
ANTIPLAGIAT_API_KEY = '12025e688e01b9b32359f66fd9db1aed'

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне текст, и я проверю его на уникальность.")

def check_plagiarism(text, message):
    response = requests.post(
        'https://api.text.ru/post',
        data={
            'text': text,
            'userkey': ANTIPLAGIAT_API_KEY,
            'visible': 'vis_on'
        }
    )

    if response.status_code == 200:
        result = response.json()
        if 'text_uid' in result:
            uid = result['text_uid']
            bot.reply_to(message, f"Текст принят на проверку. ID: {uid}. Ожидайте...")

            time.sleep(30)
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
                    user_data[message.chat.id] = {
                        'unique_percent': result_data['text_unique'],
                        'text': text
                    }
                    msg = bot.reply_to(message, f"Уникальность: {result_data['text_unique']}%\nВведите ваше ФИО:")
                    bot.register_next_step_handler(msg, process_name)
                else:
                    bot.reply_to(message, "Ошибка получения результата")
            else:
                bot.reply_to(message, "Ошибка запроса результата")
        else:
            bot.reply_to(message, "Ошибка отправки текста")
    else:
        bot.reply_to(message, "Ошибка соединения")

def process_name(message):
    user_id = message.chat.id
    user_data[user_id]['name'] = message.text
    msg = bot.reply_to(message, "Введите название работы:")
    bot.register_next_step_handler(msg, process_project)

def process_project(message):
    user_id = message.chat.id
    user_data[user_id]['project'] = message.text
    msg = bot.reply_to(message, "Введите тип работы:")
    bot.register_next_step_handler(msg, process_type)

def process_type(message):
    user_id = message.chat.id
    user_data[user_id]['type'] = message.text
    msg = bot.reply_to(message, "Введите подразделение:")
    bot.register_next_step_handler(msg, process_department)

def process_department(message):
    user_id = message.chat.id
    user_data[user_id]['department'] = message.text
    generate_certificate(user_id)
    
    with open("output.pdf", "rb") as file:
        bot.send_document(message.chat.id, file)
    
    os.remove("output.pdf")
    del user_data[user_id]

def generate_certificate(user_id):
    data = user_data[user_id]

    # Преобразуем уникальность в число
    unique_percent = float(data['unique_percent'])

    # Открываем шаблон PDF
    template = PdfReader("СПРАВКА.pdf")
    writer = PdfWriter()

    # Берем первую страницу шаблона
    page = template.pages[0]

    # Создаем новый PDF с текстом
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    try:
        can.setFont("DejaVuSans-Bold", 21)  # Используем жирный шрифт и размер 21
    except:
        can.setFont("Helvetica-Bold", 21)

    # Добавляем текст на нужные позиции с координатами
    can.drawString(59.53, 620.93, f"Автор работы: {data['name']}")
    can.drawString(59.53, 580.53, f"Название работы: {data['project']}")
    can.drawString(59.53, 540.13, f"Тип работы: {data['type']}")
    can.drawString(59.53, 500.73, f"Подразделение: {data['department']}")
    can.drawString(108.97, 350.73, f"Оригинальность: {unique_percent}%")
    can.drawString(108.97, 390.06, f"Совпадение: {100 - unique_percent}%")
    can.drawString(109.73, 280.03, f"ДАТА ПРОВЕРКИ: {time.strftime('%d.%m.%Y')}")

    can.save()
    
    # Перемещаем указатель в начало потока
    packet.seek(0)

    # Загружаем созданный PDF
    new_pdf = PdfReader(packet)
    overlay = new_pdf.pages[0]

    # Накладываем текст поверх шаблона
    page.merge_page(overlay)

    # Добавляем измененную страницу в новый PDF
    writer.add_page(page)

    # Сохраняем результат
    with open("output.pdf", "wb") as output_pdf:
        writer.write(output_pdf)



@bot.message_handler(func=lambda message: True)
def handle_text(message):
    check_plagiarism(message.text, message)

if __name__ == '__main__':
    bot.polling()
