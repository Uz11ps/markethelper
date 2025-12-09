import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple

import requests
from http.cookiejar import MozillaCookieJar, Cookie
from fastapi import HTTPException

from backend.models.file import AccessFile
from backend.models import AccessGroup, Subscription, User

logger = logging.getLogger(__name__)

COOKIE_DIR = "/app/cookie"
os.makedirs(COOKIE_DIR, exist_ok=True)

# URL можно настроить через переменные окружения
SALESFINDER_LOGIN_URL = os.getenv("SALESFINDER_LOGIN_URL", "https://salesfinder.ru/api/user/signIn")
SALESFINDER_CHECK_URL = os.getenv("SALESFINDER_CHECK_URL", "https://salesfinder.ru/api/user/getUser")


class FileService:
    @staticmethod
    async def get_group_file(group_id: int) -> AccessFile:
        """
        Выбирает файл для группы (равномерно, prefer unlocked).
        """
        now = datetime.now(timezone.utc)
        candidates = await AccessFile.filter(group_id=group_id).order_by("last_updated").all()
        if not candidates:
            raise HTTPException(404, "Нет файлов для этой группы")
        for f in candidates:
            if not f.locked_until or f.locked_until < now:
                return f
        return candidates[0]

    @staticmethod
    async def get_user_file_by_tg(tg_id: int) -> AccessFile:
        """
        Возвращает AccessFile для активной подписки пользователя (по tg_id).
        Берёт первую подписку с end_date > now.
        """
        user = await User.get_or_none(tg_id=tg_id)
        if not user:
            raise HTTPException(404, "Пользователь не найден")

        now = datetime.now(timezone.utc)
        subscription = await Subscription.filter(user_id=user.id, end_date__gt=now).prefetch_related("group").first()
        if not subscription or not subscription.group:
            raise HTTPException(404, "Активная подписка не найдена")

        file = await FileService.get_group_file(subscription.group.id)
        return file

    @staticmethod
    async def read_file_content(file: AccessFile) -> str:
        if not file.path or not os.path.exists(file.path) or os.path.getsize(file.path) == 0:
            raise HTTPException(404, "Файл отсутствует или пуст")
        with open(file.path, "r", encoding="utf-8") as fh:
            return fh.read()

    @staticmethod
    async def update_cookies(file: AccessFile, cookies_str: str, user_id: int | None = None) -> AccessFile:
        """
        Перезаписать куки контентом cookies_str (строка в netscape / текстовом формате).
        """
        if not file.path:
            file.path = os.path.join(COOKIE_DIR, f"{file.id}.txt")
        with open(file.path, "w", encoding="utf-8") as fh:
            fh.write(cookies_str)

        file.last_updated = datetime.now(timezone.utc)
        file.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        await file.save()
        return file

    @staticmethod
    async def create_empty_cookie_file(file: AccessFile, filename: str | None = None) -> AccessFile:
        """
        Создает пустой файл куков без авторизации на внешнем сервисе.
        Файл можно заполнить вручную позже.
        """
        if filename:
            cookie_filename = filename
        elif file.path:
            cookie_filename = os.path.basename(file.path)
        else:
            cookie_filename = f"{file.id}.txt"

        cookie_file_path = os.path.join(COOKIE_DIR, cookie_filename)
        
        # Создаем пустой файл куков
        jar = MozillaCookieJar(cookie_file_path)
        try:
            jar.save(ignore_discard=True, ignore_expires=True)
        except Exception as e:
            raise HTTPException(500, f"Не удалось создать файл куков: {e}")

        file.path = cookie_file_path
        file.last_updated = datetime.now(timezone.utc)
        file.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        await file.save()
        
        logger.info(f"Создан пустой файл куков для файла {file.id}: {cookie_file_path}")
        return file

    @staticmethod
    async def generate_and_save_cookies(file: AccessFile, filename: str | None = None) -> AccessFile:
        if not file.login or not file.password:
            raise HTTPException(400, "У файла нет логина или пароля")

        # Выбираем имя файла
        if filename:
            cookie_filename = filename
        elif file.path:
            cookie_filename = os.path.basename(file.path)
        else:
            cookie_filename = f"{file.id}.txt"

        cookie_file_path = os.path.join(COOKIE_DIR, cookie_filename)
        jar = MozillaCookieJar(cookie_file_path)

        session = requests.Session()
        session.cookies = jar

        logger.info(f"Попытка авторизации на {SALESFINDER_LOGIN_URL} для файла {file.id}")
        try:
            resp = session.post(
                SALESFINDER_LOGIN_URL,
                json={"user_email_address": file.login, "user_password": file.password},
                timeout=15,
            )
            logger.info(f"Ответ от {SALESFINDER_LOGIN_URL}: статус {resp.status_code}")
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(503, f"Не удалось подключиться к сервису авторизации. Проверьте доступность {SALESFINDER_LOGIN_URL}. Ошибка: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise HTTPException(504, f"Превышено время ожидания ответа от сервиса авторизации. Ошибка: {str(e)}")
        except Exception as e:
            raise HTTPException(500, f"Ошибка запроса при логине: {str(e)}")

        if resp.status_code == 404:
            raise HTTPException(
                404, 
                f"Сервис авторизации недоступен (404). "
                f"Возможно, URL изменился или сервис временно недоступен. "
                f"Проверьте URL: {SALESFINDER_LOGIN_URL}. "
                f"Ответ сервера: {resp.text[:500] if resp.text else 'Пустой ответ'}"
            )
        elif resp.status_code not in (200, 201):
            error_text = resp.text[:500] if resp.text else "Нет деталей ошибки"
            raise HTTPException(
                401, 
                f"Ошибка авторизации на salesfinder.ru (HTTP {resp.status_code}): {error_text}"
            )

        try:
            data = resp.json()
        except Exception:
            data = {}

        if not any(c.name == "connect.sid" for c in session.cookies):
            connect_sid = data.get("sid") or data.get("connect.sid")
            if connect_sid:
                cookie = Cookie(
                    version=0,
                    name="connect.sid",
                    value=str(connect_sid),
                    port=None,
                    port_specified=False,
                    domain="salesfinder.ru",
                    domain_specified=True,
                    domain_initial_dot=False,
                    path="/",
                    path_specified=True,
                    secure=False,
                    expires=None,
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest={},
                    rfc2109=False,
                )
                session.cookies.set_cookie(cookie)

        try:
            session.cookies.save(ignore_discard=True, ignore_expires=True)
        except Exception as e:
            raise HTTPException(500, f"Не удалось сохранить куки: {e}")

        file.path = cookie_file_path
        file.last_updated = datetime.now(timezone.utc)
        file.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        await file.save()
        return file

    @staticmethod
    async def regen_user_file_by_tg(tg_id: int, filename: str | None = None) -> AccessFile:
        file = await FileService.get_user_file_by_tg(tg_id)
        file.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
        await file.save()

        # если filename не передан → возьмем basename(file.path)
        if not filename and file.path:
            filename = os.path.basename(file.path)

        file = await FileService.generate_and_save_cookies(file, filename=filename)
        return file
    
    @staticmethod
    async def is_cookie_valid(file: AccessFile) -> Tuple[bool, str]:
        if not file.path or not os.path.exists(file.path):
            return False, "Файл куков отсутствует"

        jar = MozillaCookieJar(file.path)
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
        except Exception as e:
            return False, f"Не удалось загрузить куки: {e}"

        if not any(c.name == "connect.sid" for c in jar):
            return False, "connect.sid отсутствует"

        session = requests.Session()
        session.cookies = jar
        try:
            r = session.get(SALESFINDER_CHECK_URL, timeout=10)
            if r.status_code == 200:
                return True, "Куки действительны"
            return False, f"Сервер отказал, код {r.status_code}"
        except Exception as e:
            return False, f"Ошибка проверки: {e}"
