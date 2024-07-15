# ShareStats - приложение для шэринга карточек достижений

ShareStats - это веб-приложение, разработанное на FastAPI, которое позволяет студентам
делиться карточками своих достижений.

## Технологии

- FastAPI
- Uvicorn
- Pydantic
- Pillow

## Установка

1. Клонируйте репозиторий:
```bash
git clone git@github.com:skypro-fastdev/sharestats.git
```

2. Перейдите в директорию проекта:
```bash
cd sharestats
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите приложение:
```bash
uvicorn main:app --port 8000
```

## Использование

После запуска приложения, оно будет доступно по адресу `http://127.0.0.1:8000`
