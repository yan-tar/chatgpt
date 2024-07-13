from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, Application
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

# токен бота
TOKEN = os.getenv('TG_TOKEN')

inline_frame = [
                [InlineKeyboardButton("\U0001F1F7\U0001F1FA", callback_data="ru"),
                InlineKeyboardButton("\U0001F1EC\U0001F1E7", callback_data="en")],
            ]
# создаем inline клавиатуру
inline_keyboard = InlineKeyboardMarkup(inline_frame)

# проверяем и создаем папку photos
photo_dir = Path("photos")
photo_dir.mkdir(exist_ok=True)

# функция-обработчик команды /start
async def start(update, context):
    await update.message.reply_text('Выберите язык / Choose your language', reply_markup=inline_keyboard)

# функция-обработчик нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # получаем callback query из update
    query = update.callback_query
    context.user_data['lang'] = query.data
    
    if context.user_data['lang'] == 'en':
      await query.edit_message_text(text=f"Welcome!")
    else:
      await query.edit_message_text(text=f"Добро пожаловать!")

# функция-обработчик команды /help
async def help(update, context):
    await update.message.reply_text('Этот бот предназначен для обучения!\u2757') # todo смайлик красного восклицательного знака

# функция-обработчик текстовых сообщений
async def text(update: Update, context):
    if context.user_data['lang'] == 'en':
      await update.message.reply_text('We’ve received a message from you!')
    else:
      await update.message.reply_text('Текстовое сообщение получено!')

# функция-обработчик сообщений с изображениями
async def image(update: Update, context):
    global photo_dir

    # получаем изображение из апдейта
    file = await update.message.photo[-1].get_file()
    
    # сохраняем изображение с уникальным именем на диск
    await file.download_to_drive(photo_dir / f"{update.message.from_user.id}-{update.message.message_id}-image.jpg")

    if context.user_data['lang'] == 'en':
      await update.message.reply_text('Photo saved!')
    else:
      await update.message.reply_text('Фотография сохранена')

# функция-обработчик голосовых сообщений
async def voice(update: Update, context):
    if context.user_data['lang'] == 'en':
      await update.message.reply_photo('image.jpg', caption='We’ve received a voice message from you!')
    else:
      await update.message.reply_photo('image.jpg', caption='Голосовое сообщение получено')

def main():

    # создаем приложение и передаем в него токен
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start)) # имя команды, которую пишем в боте; имя функции
    
    application.add_handler(CommandHandler("help", help))

    # добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))

    # добавляем CallbackQueryHandler (только для inline кнопок)
    application.add_handler(CallbackQueryHandler(button))

    # добавляем обработчик сообщений с фотографиями
    application.add_handler(MessageHandler(filters.PHOTO, image))

    # добавляем обработчик голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, voice))

    # запускаем бота (нажать Ctrl-C для остановки бота)
    application.run_polling()
    print('Бот остановлен')


if __name__ == "__main__":
    main()