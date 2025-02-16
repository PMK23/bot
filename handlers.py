from telegram import Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode
from telegram.helpers import mention_markdown
from telegram.ext import CallbackQueryHandler, CallbackContext, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils import send_telegram_message, authorize, notify_users, notify_admin_completion, notify_admin_cancellation, get_user_orders, mark_cell_green
from config import ADMIN_IDS

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Я бот для мониторинга экскурсий.')
    await authorize(update.message.chat_id)

async def help_command(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.')
        return
    await update.message.reply_text('Если у вас есть вопросы, свяжитесь с @IvanPmk: https://t.me/IvanPmk')

async def info(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    orders_info = get_user_orders(user_id)
    completed_count = 0

    if orders_info:
        message_parts = []
        for order in orders_info:
            if order:
                parts = order.split(' ')
                if len(parts) >= 4:
                    location_name = parts[0].strip()
                    date_text = parts[1].strip()
                    time_text = parts[2].strip()
                    if "ВЫПОЛНЕНО" not in order:
                        message = f"Локация: {location_name} | Дата: {date_text} | Время: {time_text}"
                        keyboard = [
                            [InlineKeyboardButton(f"Отказаться от экскурсии {location_name} {date_text} {time_text}", callback_data=f"cancel_{location_name}_{date_text}_{time_text}")],
                            [InlineKeyboardButton(f"Уведомить о выполнении", callback_data=f"complete_{location_name}_{date_text}_{time_text}")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(message, reply_markup=reply_markup)
                    else:
                        completed_count += 1

        await update.message.reply_text(f"Всего выполнено экскурсий: {completed_count}")
    else:
        await update.message.reply_text("У вас пока нет заказов.")

async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.')
        return

    await update.message.reply_text('Пожалуйста, введите текст сообщения для рассылки:')
    return BROADCAST_TEXT

async def table(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.')
        return

    await update.message.reply_text(f'Таблица пользователей и заказов:\n{spreadsheet_url}')

async def statistics(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.')
        return

    client = authorize_google_sheets()
    sheet = client.open_by_url(spreadsheet_url).sheet1
    all_values = sheet.get_all_values()
    user_count = len(all_values) - 1
    admin_count = len(ADMIN_IDS)
    completed_count = 0
    for row in all_values[1:]:
        for cell in row[3:]:
            if "ВЫПОЛНЕНО" in cell:
                completed_count += 1

    message = f"Статистика бота:\nКоличество участников: {user_count}\nКоличество администраторов: {admin_count}\nКоличество выполненных экскурсий: {completed_count}"

    for admin_id in ADMIN_IDS:
        await send_telegram_message(admin_id, message)

    await update.message.reply_text('Статистика отправлена администраторам.')

async def userstats(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    orders_info = get_user_orders(user_id)
    completed_count = 0

    if orders_info:
        message_parts = []
        for order in orders_info:
            if order:
                parts = order.split(' ')
                if len(parts) >= 4:
                    location_name = parts[0].strip()
                    date_text = parts[1].strip()
                    time_text = parts[2].strip()
                    status = "ВЫПОЛНЕНА" if "ВЫПОЛНЕНО" in order else ""
                    if status == "ВЫПОЛНЕНА":
                        completed_count += 1
                    message_parts.append(f"Локация: {location_name} | Дата: {date_text} | Время: {time_text} |{status}")

        message = "\n".join(message_parts)
        message += f"\n\nВсего выполнено экскурсий: {completed_count}"
    else:
        message = "У вас пока нет заказов."

    await update.message.reply_text(message)

async def links(update: Update, context: CallbackContext) -> None:
    links_data = [
        {"name": "НАДПИСИ НА ЧАСТЯХ КОМПАСА.docx", "url": "https://docs.google.com/document/d/1hWp9fYcy2ZbsMkCB3gY9e6AgNdoyGAsK/edit?usp=drive_link&ouid=109017548162176126049&rtpof=true&sd=true"},
        {"name": "Обновленная_версия_Памятка_Рождественская.docx", "url": "https://docs.google.com/document/d/1RGK-yIxdccM2VnUUs-CWDWf-CPdWZ5lD/edit?usp=drive_link&ouid=109017548162176126049&rtpof=true&sd=true"},
        {"name": "памятка рождестенская.wps", "url": "https://drive.google.com/file/d/13IChyyNXJHe_GpUlZKYJUqM06Ty-UcTL/view?usp=drive_link"},
        {"name": "памятка ярмарка.wps", "url": "https://drive.google.com/file/d/1icYyhIfjm8IhDsjF9TiBZBcNIPOka6yI/view?usp=drive_link"},
        {"name": "Правила для проводников.docx", "url": "https://docs.google.com/document/d/1qctS3Ny_TjxgPY_yxK6jhgUzRk5Ejb2p/edit?usp=drive_link&ouid=109017548162176126049&rtpof=true&sd=true"},
        {"name": "Приветствие.docx", "url": "https://docs.google.com/document/d/1Lh7gchHSUzn6GAT1bRv7iquGBlVWKq3W/edit?usp=drive_link&ouid=109017548162176126049&rtpof=true&sd=true"},
        {"name": "СУДЬБА НА СТАРТЕ И ФИИНИШЕ.wps", "url": "https://drive.google.com/file/d/1_WLp4CDjIMC80jIdtENr5qJFZRSzjuzR/view?usp=drive_link"},
        {"name": "ЯРМАРКА ШПАРГАЛКА.docx", "url": "https://docs.google.com/document/d/1A6DOxCx4g2TNObTrSdrk0JP79ktxXCiK/edit?usp=drive_link&ouid=109017548162176126049&rtpof=true&sd=true"},
        {"name": "NN_Yarmarka_Track 1_РЕМИКС_mono.mp3", "url": "https://drive.google.com/file/d/1ovNXBR_kDrBoIcYQVxVb1oJTM5IBWlin/view?usp=sharing"},
        {"name": "Track 1 Progulka.mp3", "url": "https://drive.google.com/file/d/1cLbZilSOtYaxZ0WrzKZ21WqN7MNF2yUq/view?usp=drive_link"}
    ]

    keyboard = []
    for link in links_data:
        keyboard.append([InlineKeyboardButton(link['name'], url=link['url'])])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите файл:", reply_markup=reply_markup)

async def monitor(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text('У вас нет прав для выполнения этой команды.')
        return

    await update.message.reply_text('Начинаю мониторинг экскурсий...')
    await authorize(update.message.chat_id)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    logger.info(f"Callback data: {data}")

    if len(data) < 4:
        logger.error(f"Неверный формат callback_data: {query.data}")
        await query.edit_message_text(text="Ошибка: неверный формат данных.")
        return

    action = data[0]
    location_name = data[1]
    date_text = data[2]
    time_text = data[3]

    if action == "take":
        user_requests[f"{location_name}_{date_text}_{time_text}"] = query.from_user.id
        admin_message = f"Пользователь {mention_markdown(query.from_user.id, query.from_user.username)} нажал кнопку 'Взять экскурсию' для {location_name} {date_text} {time_text}"
        keyboard = [
            [InlineKeyboardButton("Подтвердить экскурсию", callback_data=f"confirm_{location_name}_{date_text}_{time_text}_{query.from_user.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        for admin_id in ADMIN_IDS:
            await send_telegram_message(admin_id, admin_message, reply_markup)
        await query.edit_message_text(text=f"Вы выбрали: {location_name} {date_text} {time_text}")

        await update_google_sheet_take(query.from_user.id, query.from_user.username, location_name, date_text, time_text)

    elif action == "cancel":
        await query.edit_message_text(text=f"Пожалуйста, укажите причину отмены экскурсии {location_name} | {date_text} {time_text}.")
        context.user_data['cancel_info'] = (location_name, date_text, time_text)

    elif action == "complete":
        user_id = query.message.chat.id
        username = query.message.chat.username
        success = await mark_cell_green(user_id, location_name, date_text, time_text)
        if success:
            await query.edit_message_text(text=f"Экскурсия {location_name} {date_text} {time_text} успешно выполнена.")
            await notify_admin_completion(username, location_name, date_text, time_text)
        else:
            await query.edit_message_text(text=f"Ошибка при выполнении экскурсии {location_name} {date_text} {time_text}.")

    elif action == "confirm":
        user_id = int(data[4])
        await update_google_sheet_register(user_id, None, location_name, date_text, time_text)
        await send_telegram_message(user_id, f"Ваша экскурсия {location_name} {date_text} {time_text} подтверждена.")
        await query.edit_message_text(text=f"Экскурсия {location_name} {date_text} {time_text} подтверждена.")

async def handle_cancel_reason(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    reason = update.message.text
    cancel_info = context.user_data.get('cancel_info')

    if cancel_info:
        location_name, date_text, time_text = cancel_info
        admin_message = f"Пользователь {mention_markdown(user_id, update.message.from_user.username)} хочет отменить экскурсию {location_name} {date_text} {time_text}. Причина: {reason}"
        for admin_id in ADMIN_IDS:
            await send_telegram_message(admin_id, admin_message)
        await update.message.reply_text(text="Ваш запрос на отмену отправлен администратору.")

        success = await remove_data_from_sheet(user_id, update.message.from_user.username, location_name, date_text, time_text)
        if success:
            await send_telegram_message(user_id, f"Ваша экскурсия {location_name} {date_text} {time_text} успешно отменена.")
        else:
            await update.message.reply_text(text=f"Ваша экскурсия {location_name} {date_text} {time_text} успешно отменена.")
