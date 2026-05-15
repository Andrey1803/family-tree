# Безопасность

## Если репозиторий был публичным

Пароли и данные могли попасть в историю Git на GitHub. Рекомендуется:

1. **Сменить пароли** всех пользователей (веб, sync_server, Railway).
2. Задать новый **`SECRET_KEY`** на Railway для `web` и `sync_server`.
3. Не коммитить `data/`, `users.json`, `*.db`, логи — см. `.gitignore`.
4. Использовать `.env` локально (образец: `.env.example`).

## Переменные окружения (production)

| Переменная | Назначение |
|------------|------------|
| `SECRET_KEY` | Сессии Flask (обязательно) |
| `SESSION_COOKIE_SECURE=true` | HTTPS |
| `CORS_ORIGINS` | Домены фронта через запятую |
| `FLASK_DEBUG=false` | Без отладочной консоли |
| `DATA_DIR` | Путь к данным на volume |

## Скрипты загрузки

```bash
set FAMILY_TREE_LOGIN=Ваш логин
set FAMILY_TREE_PASSWORD=ваш_пароль
python upload_all_photos.py
```
