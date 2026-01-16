# ChatList - GitHub Pages

Эта папка содержит статический сайт для GitHub Pages.

## Файлы

- `index.html` - главная страница
- `style.css` - стили
- `logo.png` - логотип приложения

## Локальный просмотр

Для просмотра сайта локально:

1. Откройте `index.html` в браузере
2. Или запустите локальный сервер:

```powershell
# Python 3
python -m http.server 8000

# Затем откройте http://localhost:8000
```

## Публикация

Сайт автоматически публикуется на https://evgen018.github.io/ChatList/ при пуше в ветку `main`.

Настройки GitHub Pages:
- Source: Deploy from a branch
- Branch: `main`
- Folder: `/docs`

## Обновление

При изменении версии приложения:

1. Обновите версию в `index.html` (поиск по тексту "1.0.4")
2. Обновите ссылки на скачивание
3. Добавьте новые возможности в секцию "Возможности"
4. Закоммитьте и запушьте изменения

## Скриншоты

Для улучшения сайта рекомендуется добавить скриншоты:

```powershell
# Создайте папку screenshots
New-Item -ItemType Directory -Path docs\screenshots

# Добавьте скриншоты приложения
# - main-window.png
# - dark-theme.png
# - models-tab.png
# и т.д.
```

Затем обновите `index.html`, заменив иконку в hero-секции на реальные скриншоты.
