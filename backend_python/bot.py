import os
import wave
import re
import json
import smtplib
from email.mime.text import MIMEText
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment

# 8168509436:AAH0BsRBcRYBjp_SeAeZasUTZuptTj2sz3c
TOKEN = "7266088345:AAHHKBuOXDnpXtgJ92jwhYXXs9XC0ePzkn8"

SMTP_SERVER = 'smtp.mail.ru'
SMTP_PORT = 465
EMAIL_ADDRESS = 'erguxxbotting@mail.ru'
EMAIL_PASSWORD = 'zvvPzTUB4neugrpcf2qt'
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

model = Model("vosk-model-small-ru")

CHOOSE_ACTION, ENTER_CONTRACT_NUMBER, ENTER_CONTACT_INFO, ENTER_EMAIL_ADDRESS, ENTER_SUBJECT, ENTER_BODY = range(6)

# Функция для отправки электронного письма
def send_email(subject: str, body: str, to_email: str) -> bool:
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
            return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Функция для распознавания речи и перевода в текст
def transcribe_audio(file_path):
    recognizer = KaldiRecognizer(model, 16000)
    result_text = ""

    with wave.open(file_path, "rb") as audio_file:
        if audio_file.getframerate() != 16000:
            print(f"Ошибка: частота дискретизации файла {file_path} не 16000 Гц.")
            return ""

        while True:
            data = audio_file.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                result_text += result["text"] + " "
        result = json.loads(recognizer.FinalResult())
        result_text += result["text"]

    return result_text.strip()

# Функция для конвертации OGG в WAV
def convert_ogg_to_wav(ogg_path, wav_path):
    audio = AudioSegment.from_file(ogg_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(wav_path, format="wav")

# Определение намерения
def determine_intent(text):
    text = text.lower().strip()
    intents = {
    "войти как клиент ттк": "Вход как клиент ТТК",
    "вход в аккаунт": "Вход как клиент ТТК",
    "доступ к аккаунту ттк": "Вход как клиент ТТК",
    "зайти в аккаунт": "Вход как клиент ТТК",
    "авторизоваться": "Вход как клиент ТТК",
    "получить доступ к аккаунту": "Вход как клиент ТТК",
    "войти в профиль": "Вход как клиент ТТК",
    "войти в личный кабинет": "Вход как клиент ТТК",

    "заключить новый договор": "Заключение нового договора",
    "новый договор": "Заключение нового договора",
    "подключить услугу": "Заключение нового договора",
    "хочу новый договор": "Заключение нового договора",
    "оформить подключение": "Заключение нового договора",
    "оформить договор": "Заключение нового договора",
    "подключение услуги": "Заключение нового договора",
    "подключить интернет": "Заключение нового договора",
    "новый контракт": "Заключение нового договора",
    "оформить контракт": "Заключение нового договора",

    "отправить письмо": "Отправка письма",
    "отправить сообщение": "Отправка письма",
    "написать письмо": "Отправка письма",
    "написать сообщение": "Отправка письма",
    "послать письмо": "Отправка письма",
    "направить письмо": "Отправка письма",
    "отправить email": "Отправка письма",
    "написать email": "Отправка письма",
    "отправка email": "Отправка письма",
    "отправить электронное письмо": "Отправка письма",
    "написать электронное письмо": "Отправка письма"
}
    return intents.get(text, "Неопределенное намерение")

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return CHOOSE_ACTION

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Войти как клиент ТТК")],
        [KeyboardButton("Заключить новый договор")],
        [KeyboardButton("Отправить письмо")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Здравствуйте! Что бы вы хотели:", reply_markup=reply_markup)
    return CHOOSE_ACTION

# Обработка текстовых сообщений для выбора действия
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    if user_text == "войти как клиент ттк":
        await update.message.reply_text("Введите, пожалуйста, номер вашего договора.")
        return ENTER_CONTRACT_NUMBER
    elif user_text == "заключить новый договор":
        await update.message.reply_text("Укажите ваш контактный номер и адрес для подключения услуги.")
        return ENTER_CONTACT_INFO
    elif user_text == "отправить письмо":
        await update.message.reply_text("Введите адрес электронной почты получателя.")
        return ENTER_EMAIL_ADDRESS
    else:
        await update.message.reply_text("Пожалуйста, выберите одно из предложенных действий.")
        return CHOOSE_ACTION

# Обработка ввода номера договора
async def enter_contract_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contract_number = update.message.text
    await update.message.reply_text(f"Спасибо! Вы указали номер договора: {contract_number}. Мы начнем процесс входа.")
    return CHOOSE_ACTION

# Обработка ввода контактных данных для нового договора
async def enter_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_info = update.message.text
    await update.message.reply_text(f"Спасибо! Контактные данные получены: {contact_info}.")
    return CHOOSE_ACTION

# Обработка ввода адреса электронной почты
async def enter_email_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text

    # Проверка адреса электронной почты
    if not re.match(EMAIL_REGEX, email):
        await update.message.reply_text("Некорректный адрес электронной почты. Попробуйте снова.")
        return ENTER_EMAIL_ADDRESS

    context.user_data['email'] = email
    await update.message.reply_text("Введите тему письма.")
    return ENTER_SUBJECT

# Обработка ввода темы письма
async def enter_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text
    context.user_data['subject'] = subject
    await update.message.reply_text("Введите сообщение.")
    return ENTER_BODY

# Обработка ввода тела письма и отправка
async def enter_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    body = update.message.text
    email = context.user_data.get('email')
    subject = context.user_data.get('subject')

    if send_email(subject, body, email):
        await update.message.reply_text(f"Письмо отправлено на {email}!")
    else:
        await update.message.reply_text("Не удалось отправить письмо.")
    return CHOOSE_ACTION

# Обработка голосовых сообщений
async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    ogg_path = "voice.ogg"
    wav_path = "voice.wav"
    await file.download_to_drive(ogg_path)

    convert_ogg_to_wav(ogg_path, wav_path)

    if os.path.exists(wav_path):
        print(f"Файл {wav_path} успешно создан.")
    else:
        print(f"Ошибка: файл {wav_path} не найден.")
        await update.message.reply_text("Не удалось обработать голосовое сообщение.")
        return

    text = transcribe_audio(wav_path)
    await update.message.reply_text(f"Распознанный текст: {text}")

    intent = determine_intent(text)
    await update.message.reply_text(f"Определенное намерение: {intent}")

    if intent == "Вход как клиент ТТК":
        await update.message.reply_text("Введите, пожалуйста, номер вашего договора.")
        return ENTER_CONTRACT_NUMBER
    elif intent == "Заключение нового договора":
        await update.message.reply_text("Укажите ваш контактный номер и адрес для подключения услуги.")
        return ENTER_CONTACT_INFO
    elif intent == "Отправка письма":
        await update.message.reply_text("Введите адрес электронной почты получателя.")
        return ENTER_EMAIL_ADDRESS
    else:
        await update.message.reply_text("Не удалось определить намерение. Попробуйте еще раз.")
        return CHOOSE_ACTION

# Основная функция для запуска бота
def main():
    application = Application.builder().token(TOKEN).build()

    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            ENTER_CONTRACT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contract_number)],
            ENTER_CONTACT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact_info)],
            ENTER_EMAIL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email_address)],
            ENTER_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_subject)],
            ENTER_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_body)],
        },
        fallbacks=[CommandHandler("start", start),
                   CommandHandler("back", back)]
    )

    # Обработчик голосовых сообщений
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))

    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
