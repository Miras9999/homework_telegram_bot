import os
import telegram
import time
import requests
import logging

from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import (RequestConnectionError,
                        StatusCodeExceptions,
                        UnknownHomeWorkStatus)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Checking for required data."""
    if not (PRACTICUM_TOKEN or TELEGRAM_TOKEN or TELEGRAM_CHAT_ID):
        return False
    else:
        return True


def send_message(bot, message):
    """Function for send message."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug('Сообщение отправлено')


def get_api_answer(timestamp):
    """API response function."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})

    except requests.RequestException as error:
        logging.error('Ошибка запроса/соединения', error)
        raise RequestConnectionError('Ошибка запроса/соединения') from error

    if response.status_code != HTTPStatus.OK:
        raise StatusCodeExceptions(
            'Некорректный ответ от API!'
        )

    return response.json()


def check_response(response):
    """Checking for the necessary keys."""
    if type(response) != dict:
        raise TypeError('Ожидался словарь')

    if response.get('homeworks') is None:
        logging.error('Ключ не найден')
        raise KeyError('Ключ не найден')

    if type(response.get('homeworks')) != list:
        logging.error('Неверный тип данных')
        raise TypeError('Неизвестный тип в значении ключа homeworks')

    return response.get('homeworks')[0]


def parse_status(homework):
    """Formation of a message based on the status summary."""
    if len(homework) == 0:
        logging.debug('Статус прежний')

    if homework.get('homework_name') is None:
        raise KeyError('Ключ не найден')

    if HOMEWORK_VERDICTS.get(homework.get('status')) is None:
        raise UnknownHomeWorkStatus('Неизвестный статус работы')

    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    if check_tokens() is False:
        logging.critical('Отсутствуют обязязательные переменные окружения!')
        raise SystemExit('Отсутствуют обязязательные переменные окружения!')

    logging.debug('Можно продолжить работу')

    while True:
        try:
            response = get_api_answer(timestamp=timestamp)
            homework = check_response(response=response)
            send_message(bot=bot, message=parse_status(homework=homework))
            timestamp = response.get('current_date')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot=bot, message=message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=('%(asctime)s, %(levelname)s, %(message)s, %(name)s'
                '%(pathname)s:%(lineno)d')
    )
    main()
