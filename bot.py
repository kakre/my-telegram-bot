from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
from threading import Timer

# Вставьте ваш токен здесь
TOKEN = '8059057105:AAGGMvW9I2vIy5Jms5x0q9X9AJY9wtOjwEc'

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Словарь для хранения информации о поездках пользователей
user_requests = {}
DRIVER_GROUP_ID = -123456789  # Замените на ID вашей группы

# Начальная функция
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    buttons = [
        [KeyboardButton("Заказать такси"), KeyboardButton("Отменить заявку")],
        [KeyboardButton("История поездок")]
    ]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Добро пожаловать, {user.first_name}!\nЯ бот DeGo. Чем могу помочь?",
                             reply_markup=ReplyKeyboardMarkup(buttons))

# Функция для приема заявок
def request_taxi(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_requests[user_id] = {'status': 'started'}
    update.message.reply_text("Пожалуйста, отправьте адрес или геолокацию.",
                              reply_markup=ReplyKeyboardRemove())
    logger.info(f"User {user_id} started a request.")

# Функция для обработки адреса
def address_received(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in user_requests and user_requests[user_id]['status'] == 'started':
        user_requests[user_id]['address'] = update.message.text
        user_requests[user_id]['status'] = 'waiting_for_car'
        user_requests[user_id]['car_info'] = "Toyota Camry, номер A123BC"
        user_requests[user_id]['price'] = "500 руб."

        order_info = user_requests[user_id]
        notify_drivers(order_info)

        # Таймер для проверки, был ли принят заказ
        Timer(60.0, check_order_status, args=[user_id, context.bot]).start()

        update.message.reply_text(f"Ваш заказ принят. {user_requests[user_id]['car_info']} скоро приедет за вами.\nЦена поездки: {user_requests[user_id]['price']}.",
                                  reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отменить заявку")], [KeyboardButton("История поездок")]]))
        logger.info(f"User {user_id} provided address: {user_requests[user_id]['address']}")

# Функция для обработки геолокации
def location_received(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in user_requests and user_requests[user_id]['status'] == 'started':
        location = update.message.location
        user_requests[user_id]['location'] = (location.latitude, location.longitude)
        user_requests[user_id]['status'] = 'waiting_for_car'
        user_requests[user_id]['car_info'] = "Toyota Camry, номер A123BC"
        user_requests[user_id]['price'] = "500 руб."

        order_info = user_requests[user_id]
        notify_drivers(order_info)

        # Таймер для проверки, был ли принят заказ
        Timer(60.0, check_order_status, args=[user_id, context.bot]).start()

        update.message.reply_text(f"Ваш заказ принят. {user_requests[user_id]['car_info']} скоро приедет за вами.\nЦена поездки: {user_requests[user_id]['price']}.",
                                  reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отменить заявку")], [KeyboardButton("История поездок")]]))
        logger.info(f"User {user_id} provided location: {user_requests[user_id]['location']}")

# Функция для уведомления водителей
def notify_drivers(order_info):
    app.bot.send_message(chat_id=DRIVER_GROUP_ID,
                         text=f"Новый заказ!\nАдрес: {order_info.get('address')}\nГеолокация: {order_info.get('location')}\nИнформация о машине: {order_info['car_info']}\nЦена: {order_info['price']}")

# Функция для проверки статуса заказа
def check_order_status(user_id, bot):
    if user_requests[user_id]['status'] == 'waiting_for_car':
        bot.send_message(chat_id=user_id,
                         text="К сожалению, сейчас высокий спрос. Просим подождать либо отменить заявку.",
                         reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отменить заявку")], [KeyboardButton("История поездок")]]))
        logger.info(f"Order for user {user_id} not taken.")

# Функция для отмены заявок
def cancel_request(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in user_requests:
        update.message.reply_text("Ваша заявка отменена.",
                                  reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Заказать такси")], [KeyboardButton("История поездок")]]))
        logger.info(f"User {user_id} canceled the request: {user_requests[user_id]}")
        del user_requests[user_id]
    else:
        update.message.reply_text("У вас нет активных заявок.")

# Функция для отображения истории поездок
def trip_history(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in user_requests:
        history = user_requests[user_id].get('history', 'Нет сохраненных поездок.')
        update.message.reply_text(f"История ваших поездок:\n{history}")
    else:
        update.message.reply_text("У вас еще нет завершенных поездок.")

# Основная логика команд и сообщений
def main() -> None:
    global app
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('^Заказать такси$'), request_taxi))
    app.add_handler(MessageHandler(filters.LOCATION, location_received))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, address_received))
    app.add_handler(MessageHandler(filters.Regex('^Отменить заявку$'), cancel_request))
    app.add_handler(MessageHandler(filters.Regex('^История поездок$'), trip_history))

    # Запуск бота
    app.run_polling()

if __name__ == '__main__':
    main()
