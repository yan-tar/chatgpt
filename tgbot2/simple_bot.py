from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from dotenv import load_dotenv
import openai
import os
import requests
import aiohttp
import json


# подгружаем переменные окружения
load_dotenv()

# передаем секретные данные в переменные
TOKEN = os.environ.get("TG_TOKEN")
GPT_SECRET_KEY = os.environ.get("GPT_SECRET_KEY")

# передаем секретный токен chatgpt
openai.api_key = GPT_SECRET_KEY


# функция для синхронного общения с chatgpt
async def get_answer(text):
    payload = {"text":text}
    response = requests.post("http://127.0.0.1:5000/api/get_answer", json=payload)
    return response.json()


# функция для асинхронного общения с сhatgpt
async def get_answer_async(text):
    payload = {"text":text}
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:5000/api/get_answer_async', json=payload) as resp:
            return await resp.json()
        
# функция для асинхронной суммаризации с помощью сhatgpt
async def get_and_save_summary_async(history, context:ContextTypes.DEFAULT_TYPE, user_id):
    payload = {"text":history}
    
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:5000/api/get_summary', json=payload) as resp:
            response =  await resp.json()
            print("У нас есть саммари:", response)
            context.bot_data[user_id]['history_summarized'] = response

def set_message_count(count:int, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in context.bot_data.keys():
        context.bot_data[update.message.from_user.id] = {}
    context.bot_data[update.message.from_user.id]['message_count'] = count
    # print("Обновлено количество сообщений")

def get_message_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return context.bot_data[update.message.from_user.id].get('message_count')

# функция-обработчик команды /start 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # при первом запуске бота добавляем этого пользователя в словарь
    set_message_count(3, update, context)

    # создаем массив для истории сообщений
    user_id = update.message.from_user.id
    if 'history' not in context.bot_data[user_id]:
        context.bot_data[user_id]['history'] = []
    if 'history_summarized' not in context.bot_data[user_id]:
        context.bot_data[user_id]['history_summarized'] = ''
    
    # возвращаем текстовое сообщение пользователю
    await update.message.reply_text('Задайте любой вопрос ChatGPT')


# функция-обработчик команды /data 
async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # создаем json и сохраняем в него словарь context.bot_data
    with open('data.json', 'w', encoding='utf-8') as fp:
        json.dump(context.bot_data, fp, ensure_ascii=False, indent=4)
    
    # возвращаем текстовое сообщение пользователю
    await update.message.reply_text('Данные сгружены')

# сохраняем сообщение в историю и делаем запрос для саммаризации
async def save_msg_and_reply(msg:str, reply:str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    str = "Вопрос: " + msg + "\nОтвет: " + reply
    context.bot_data[user_id]['history'].append(str) 

    context.bot_data[user_id]['history'] = context.bot_data[user_id]['history'][-5:]

    history_joined = '\n'.join([f'{message}' for message in context.bot_data[user_id]['history']])
    await get_and_save_summary_async(history_joined, context, user_id)
    
    # print(str)


# функция-обработчик текстовых сообщений
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message_count = get_message_count(update, context)
    # проверка доступных запросов пользователя
    if message_count > 0:

        # выполнение запроса в chatgpt
        first_message = await update.message.reply_text('Ваш запрос обрабатывается, пожалуйста подождите...')
        # получаем ответ от гпт, используя асинхронную функцию
        res = await get_answer_async(update.message.text)
        await save_msg_and_reply(update.message.text, res['message'], update, context)
        
        await context.bot.edit_message_text(text=res['message'], chat_id=update.message.chat_id, message_id=first_message.message_id)

        # уменьшаем количество доступных запросов на 1
        message_count-=1
        set_message_count(message_count, update, context)
    
    else:

        # сообщение если запросы исчерпаны
        await update.message.reply_text('Ваши запросы на сегодня исчерпаны')


# функция, которая будет запускаться раз в сутки для обновления доступных запросов
async def callback_daily(context: ContextTypes.DEFAULT_TYPE):

    # проверка базы пользователей
    if context.bot_data != {}:

        # проходим по всем пользователям в базе и обновляем их доступные запросы
        for key in context.bot_data:
            context.bot_data[key]['message_count'] = 5
        print('Запросы пользователей обновлены')
    else:
        print('Не найдено ни одного пользователя')

# показываем историю
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Вот ваша история:')
    history = context.bot_data[update.message.from_user.id]['history']
    
    for item in history:
        await update.message.reply_text(item)

# возвращаем количество оставшихся запросов
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):   
    count = get_message_count(update, context)
    await update.message.reply_text(f'Осталось запросов: {count}')

def main():

    # создаем приложение и передаем в него токен бота
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    # создаем job_queue 
    job_queue = application.job_queue
    job_queue.run_repeating(callback_daily, # функция обновления базы запросов пользователей
                            interval=60,    # интервал запуска функции (в секундах)
                            first=10)       # первый запуск функции (через сколько секунд)

    # добавление обработчиков
    application.add_handler(CommandHandler("start", start, block=True))
    application.add_handler(CommandHandler("data", data, block=True))
    application.add_handler(CommandHandler("status", status, block=True))
    application.add_handler(CommandHandler("history", history, block=True))
    application.add_handler(MessageHandler(filters.TEXT, text, block=True))

    # запуск бота (нажать Ctrl+C для остановки)
    application.run_polling()
    print('Бот остановлен')


if __name__ == "__main__":
    main()