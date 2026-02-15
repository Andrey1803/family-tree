# Подготовка к релизу

## Чек-лист перед v1.0

- [ ] Обновить `version.py` (__version__ = "1.0.0")
- [ ] Обновить `docs/CHANGELOG.md` — указать дату релиза
- [ ] Проверить `.gitignore` — данные пользователей не попадают в репозиторий
- [ ] Протестировать desktop: запуск, вход, дерево, сохранение, экспорт CSV, протокол derevo://
- [ ] Протестировать web: запуск, вход, дерево, редактирование, скачивание desktop
- [ ] Собрать exe: `pyinstaller build_exe.spec`
- [ ] Проверить exe на чистой Windows (без Python)

## Сборка .exe

```bash
pip install pyinstaller pillow
pyinstaller build_exe.spec
```

Или: `scripts\build_exe.bat`

Результат: `dist/Семейное_древо.exe`

## Состав релиза v1.0

### Вариант 1: Исходники (ZIP)

```bash
python scripts/create_release_zip.py
```

Или: `scripts\create_release_zip.bat`

Результат: `Семейное_древо_1.0.0_source.zip` (без данных и служебных папок)

### Вариант 2: Готовый .exe
- `Семейное_древо.exe` — единственный файл, Python не требуется
- При первом запуске создаёт `users.json` и файлы деревьев рядом

### Вариант 3: Веб + скачивание desktop
- Запущенный веб-сервер: кнопка «Установить приложение» → `/download/desktop` → exe или ZIP

## Ошибки exe на другом ПК

Если exe не запускается на другом компьютере:

1. **Сообщение об ошибке** — теперь exe показывает окно с текстом. Подробности пишутся в `error_log.txt` рядом с exe.

2. **Отладка** — собрать с консолью, чтобы видеть вывод:
   ```bash
   # В build_exe.spec заменить console=False на console=True
   pyinstaller build_exe.spec
   ```

3. **Типичные причины:**
   - **Антивирус** — может блокировать exe (добавить в исключения)
   - **Visual C++ Redistributable** — установить с https://aka.ms/vs/17/release/vc_redist.x64.exe
   - **Папка** — скопировать exe в обычную папку (не Program Files, не сетевой диск)
