import logging
import asyncio
from telegram import InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from config import credentials_path, spreadsheet_url, ADMIN_IDS


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def authorize_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    return client


async def send_telegram_message(chat_id, text, reply_markup=None):
    try:
        await application.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Сообщение отправлено пользователю {chat_id}: {text}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")


async def notify_users(change, location_name):
    message = f"Изменение в экскурсии: {location_name} - {change}"
    for user_id in user_requests.values():
        if user_id not in ADMIN_IDS:
            await send_telegram_message(user_id, message)


async def notify_admin_completion(username, location_name, date_text, time_text):
    message = f"Экскурсия пользователя {username} выполнена: Локация: {location_name}, Дата: {date_text}, Время: {time_text}"
    for admin_id in ADMIN_IDS:
        await application.bot.send_message(chat_id=admin_id, text=message)


async def notify_admin_cancellation(username, location_name, date_text, time_text):
    message = f"Пользователь {username} отменил экскурсию: Локация: {location_name}, Дата: {date_text}, Время: {time_text}"
    for admin_id in ADMIN_IDS:
        await application.bot.send_message(chat_id=admin_id, text=message)


def get_user_orders(user_id):
    try:
        client = authorize_google_sheets()
        sheet = client.open_by_url(spreadsheet_url).sheet1

        cell = sheet.find(str(user_id))
        if cell:
            row_values = sheet.row_values(cell.row)
            orders = row_values[3:]
            return orders
        else:
            return []
    except Exception as e:
        logger.error(f"Ошибка при получении информации о заказах пользователя {user_id}: {e}")
        return []


async def mark_cell_green(user_id, location_name, date_text, time_text):
    try:
        client = authorize_google_sheets()
        sheet = client.open_by_url(spreadsheet_url).sheet1

        cell = sheet.find(str(user_id))
        if cell:
            row_values = sheet.row_values(cell.row)
            for i, value in enumerate(row_values[3:]):
                if f"{location_name} {date_text} {time_text}" in value:
                    cell_address = f"{chr(65 + i + 3)}{cell.row}"
                    new_value = f"{value} ВЫПОЛНЕНО"
                    sheet.update_cell(cell.row, i + 4, new_value)
                    sheet.format(cell_address, {
                        "backgroundColor": {
                            "red": 0,
                            "green": 1,
                            "blue": 0
                        }
                    })
                    return True
            return False
        else:
            return False
    except Exception as e:
        logger.error(f"Error marking cell green for user {user_id}: {e}")
        return False

# Функция для удаления данных из Google Sheets
async def remove_data_from_sheet(user_id, username, location_name, date_text, time_text):
    try:
        client = authorize_google_sheets()
        sheet = client.open_by_url(spreadsheet_url).sheet1

        cell = sheet.find(str(user_id))
        if cell:
            row_values = sheet.row_values(cell.row)
            for i, value in enumerate(row_values[3:]):
                if f"{location_name} {date_text} {time_text}" in value:
                    sheet.update_cell(cell.row, i + 4, "")
                    await notify_admin_cancellation(username, location_name, date_text, time_text)
                    return True
            return False
        else:
            return False
    except Exception as e:
        logger.error(f"Error removing data from the sheet for user {user_id}: {e}")
        return False
