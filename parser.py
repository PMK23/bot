import logging
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import send_telegram_message, notify_users
from config import ADMIN_IDS


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


async def login(driver, username, password):
    try:
        login_input = WebDriverWait(driver, 11).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="login"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", login_input)
        login_input.send_keys(username)

        password_input = WebDriverWait(driver, 11).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", password_input)
        password_input.send_keys(password)

        login_button = WebDriverWait(driver, 11).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/form/button'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        login_button.click()

        WebDriverWait(driver, 11).until(EC.visibility_of_element_located((By.XPATH, '/html/body/section/span[1]')))
    except Exception as e:
        logger.error("Ошибка во время авторизации:", exc_info=e)


async def authorize(chat_id):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Firefox(options=options)

    try:
        driver.get('https://mobex-farolero.ru/event/')
        await login(driver, 'Novgorod1', '71nn')
        await parse_location(driver, "Рождественская", chat_id)

        driver.find_element(By.XPATH, '/html/body/section/button').click()
        await asyncio.sleep(10)

        driver.get('https://mobex-farolero.ru/event/')
        await login(driver, 'Novgorod2', '72nn')
        await parse_location(driver, "Ярмарка", chat_id)
        driver.find_element(By.XPATH, '/html/body/section/button').click()
        await asyncio.sleep(10)
    except Exception as e:
        logger.exception("Ошибка во время авторизации или парсинга:")
    finally:
        driver.quit()


async def parse_location(driver, location_name, chat_id):
    global previous_excursions
    location = driver.find_element(By.XPATH, '/html/body/section/span[1]').text
    logger.info(f"Мониторинг локации {location}...")

    rows = driver.find_elements(By.XPATH, '/html/body/section/div[3]/div/table/tbody/tr')
    if not rows:
        await send_telegram_message(chat_id, "Нет новых экскурсий.")
        return

    excursions = []

    for row in rows:
        try:
            date_text = row.find_element(By.XPATH, './td[1]').text
            time_text = row.find_element(By.XPATH, './td[2]').text
            tickets_text = row.find_element(By.XPATH, './td[3]').text
            languages_text = row.find_element(By.XPATH, './td[4]').text

            excursion_data = (f"{date_text}: {time_text} | {tickets_text} | {languages_text}")
            excursions.append(excursion_data)

            message = (f"Локация: {location_name}\n"
                       f"{date_text}: {time_text} | {tickets_text} | {languages_text}.")

            keyboard = [
                [InlineKeyboardButton("Взять экскурсию", callback_data=f"take_{location_name}_{date_text}_{time_text}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            logger.info(f"Отправляю сообщение с кнопками: {message}")
            await send_telegram_message(chat_id, message, reply_markup)
        except Exception as e:
            logger.error(f"Ошибка при парсинге строки: {e}")

    if location_name not in previous_excursions:
        previous_excursions[location_name] = excursions
    else:
        previous_data = previous_excursions[location_name]
        if excursions != previous_data:
            changes = set(excursions) - set(previous_data)
            for change in changes:
                await notify_users(change, location_name)
            previous_excursions[location_name] = excursions
parser.py