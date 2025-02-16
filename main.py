import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start, info, help_command, broadcast, table, statistics, userstats, links, monitor, button, handle_cancel_reason
from utils import error_handler
from config import telegram_token, ADMIN_IDS


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

application = ApplicationBuilder().token(telegram_token).build()

# Добавление обработчиков
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('info', info))
application.add_handler(CommandHandler('help', help_command))
application.add_handler(CommandHandler('broadcast', broadcast))
application.add_handler(CommandHandler('table', table))
application.add_handler(CommandHandler('statistics', statistics))
application.add_handler(CommandHandler('userstats', userstats))
application.add_handler(CommandHandler('file', links))
application.add_handler(CommandHandler('monitor', monitor))
application.add_handler(CallbackQueryHandler(button, pattern=r'^(cancel|complete|take|confirm)_'))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cancel_reason))
application.add_error_handler(error_handler)

if __name__ == '__main__':
    application.run_polling()
