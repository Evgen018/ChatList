# 📌 Пошаговый апдейт версии (GitHub Release + GitHub Pages)

## ✅ 0) Подготовка

```powershell
# Перейдите в корень репозитория
Set-Location "D:\AI\Cursor\Curs_Cursor\ChatList"

# Обновите зависимости (по необходимости)
pip install -r requirements.txt
```

---

## 🔢 1) Обновление версии в файлах проекта

### 1.1. Обновить версию в `version.py`

```powershell
notepad version.py
```

Поставьте:
```python
__version__ = "1.0.4"
```

### 1.2. Обновить версию в `ChatList.iss`

```powershell
notepad ChatList.iss
```

Проверьте:
```iss
#define MyAppVersion "1.0.4"
#define MyAppExeName "ChatList-v1.0.4.exe"
```

### 1.3. Проверить упоминания версии (документация)

```powershell
# Найти все упоминания версии в тексте
Select-String -Path *.md, docs\*.md, docs\index.html -Pattern "v?\d+\.\d+\.\d+" -AllMatches
```

Минимальный список мест, где обычно правится версия:
- `README.md`
- `QUICKSTART.md`
- `CHANGELOG.md`
- `RELEASE.md`
- `PUBLISH_CHECKLIST.md`
- `docs/index.html`
- `docs/README.md`
- `create_archives.ps1` (дефолтная версия)

---

## 🏗️ 2) Сборка файлов релиза

### 2.1. Сборка `.exe` (PyInstaller)

```powershell
# Активируйте venv (если используете)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

# Сборка
pyinstaller ChatList.spec
```

Проверьте:
```powershell
Get-Item "dist\ChatList-v1.0.4.exe"
```

### 2.2. Сборка инсталлятора (Inno Setup)

```powershell
& "C:\Program\ISCC.exe" "ChatList.iss"
```

Проверьте:
```powershell
Get-Item "dist\ChatList-v1.0.4-Setup.exe"
```

### 2.3. Архивы исходников (опционально)

```powershell
.\create_archives.ps1 -Version "1.0.4"
Get-Item "dist\*1.0.4-Source*"
```

---

## ✅ 3) Проверка перед релизом

```powershell
python test-db.py
```

Опционально: ручной запуск `dist\ChatList-v1.0.4.exe`.

---

## 🚀 4) GitHub Release

### 4.1. Подготовить Release Notes

Используйте шаблон:
```
templates\RELEASE_NOTES_TEMPLATE.md
```

### 4.2. Коммит + тег

```powershell
git add .
git commit -m "Подготовка к релизу v1.0.4"
git tag -a v1.0.4 -m "Релиз версии 1.0.4"
git push origin main
git push origin v1.0.4
```

### 4.3. Создать релиз на GitHub

1. https://github.com/Evgen018/ChatList/releases/new  
2. Tag: `v1.0.4`  
3. Title: `ChatList v1.0.4`  
4. Вставьте Release Notes  
5. Прикрепите файлы:
   - `dist\ChatList-v1.0.4-Setup.exe`
   - `dist\ChatList-v1.0.4.exe`
   - `dist\ChatList-v1.0.4-Source.zip` (если есть)
   - `dist\ChatList-v1.0.4-Source.tar.gz` (если есть)
   - `README.md`, `LICENSE`

---

## 🌐 5) GitHub Pages

Используйте чеклист:
```
templates\GITHUB_PAGES_UPDATE.md
```

После обновления:
```powershell
git add docs\index.html docs\README.md
git commit -m "Обновление GitHub Pages для v1.0.4"
git push origin main
```

---

## ✅ 6) Финальная проверка

```powershell
git status
```

Убедитесь, что:
- Версия совпадает в `version.py` и `ChatList.iss`
- Релиз собран в `dist\`
- GitHub Release опубликован
- GitHub Pages обновлён
