# ✅ Чеклист обновления GitHub Pages

## Обязательные правки

- [ ] `docs/index.html`
  - [ ] Обновить ссылки на скачивание:
    - `ChatList-v{VERSION}-Setup.exe`
    - `ChatList-v{VERSION}.exe`
  - [ ] Обновить текст версии на странице (кнопка и блок версии)

- [ ] `docs/README.md`
  - [ ] Обновить строку про поиск версии (текущая версия)

## Проверка

- [ ] Открыть `docs/index.html` локально и проверить отображение
- [ ] Убедиться, что ссылки на скачивание ведут на актуальный релиз

## Коммит

```powershell
git add docs\index.html docs\README.md
git commit -m "Обновление GitHub Pages для v{VERSION}"
git push origin main
```
