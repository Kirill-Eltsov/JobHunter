import telegram
from services.database import DatabaseHandler
from services.hh_service import fetch_vacancies
from datetime import datetime
import asyncio

from utils.logger import log_info

async def check_new_vacancies(bot: telegram.Bot):
    db = DatabaseHandler()
    subscriptions = db.get_all_subscriptions()
    for sub in subscriptions:
        params = {
            "keyword": sub['position'],
            "area": sub['city_id'],
            "salary_from": sub['salary_min'],
            "salary_to": sub['salary_max'],
            "date_from": sub['last_vacancy_time'].strftime("%Y-%m-%dT%H:%M:%S+0500") if sub['last_vacancy_time'] else None,  # HH.ru принимает дату в формате "YYYY-MM-DDThh:mm:ss±hhmm"
        }
        new_vacancies = await fetch_vacancies(**params)
        log_info(f"Найдено {new_vacancies['found']} новых вакансий по подписке")
        if new_vacancies['found'] != 0:
            db.update_last_vacancy_time(sub['id'])
            await send_notification(sub["user_id"], new_vacancies, bot)


async def send_notification(
    user_id: int,
    vacancies: list[dict],
    bot: telegram.Bot
) -> bool:
    """
    Отправляет пользователю уведомления о новых вакансиях.
    
    :param user_id: ID пользователя в Telegram
    :param vacancies: Список вакансий в формате [{"title": str, "url": str, ...}, ...]
    :param bot: Экземпляр телеграм бота
    :return: True если отправка прошла успешно, False при ошибке
    """
    if not vacancies:
        return True  # Нет вакансий - не считается ошибкой

    try:
        # Формируем сообщение
        message_lines = [
            "🔔 <b>Новые вакансии для вас:</b>",
            *[f"<a href='{vac['alternate_url']}'>{vac['name']}</a>" for vac in vacancies["items"]],
            f"Всего найдено: {vacancies['found']}"
        ]
        message = "\n".join(message_lines)

        # Отправляем сообщение
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode=telegram.constants.ParseMode.HTML,
            disable_web_page_preview=True
        )
        return True

    except telegram.error.BadRequest as e:
        print(f"User {user_id} blocked the bot or chat doesn't exist: {e}")
    except Exception as e:
        print(f"Error sending notification to user {user_id}: {e}")
    
    return False

async def periodic_checker(application):
    """Фоновая задача для периодической проверки вакансий"""
    while True:
        try:
            log_info(f"Поиск новых вакансий...")
            await check_new_vacancies(application.bot)  # Передаем бота в функцию проверки
        except Exception as e:
            print(f"Error in periodic_checker: {e}")
        await asyncio.sleep(60)  # Проверка каждый час

async def post_init(application):
    """Запускает фоновые задачи после старта бота"""
    asyncio.create_task(periodic_checker(application))