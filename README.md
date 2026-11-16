# STAG: конспекты и партия голосовых для ноутбука

`analysis_2020_2021/` содержит подробные разборы по периодам. Папка `STAG_SECOND_CHANNEL/voice_messages/` содержит только 100 голосовых второго канала: **позиции 601–700** в списке уникальных голосовых, отсортированном по ID сообщения. Диапазон ID: **10991–11349**. Файл `batch_601_700.json` связывает каждую позицию с ID, датой, автором, аудиофайлом и SHA-256. Минимальная база `knowledge/chat.sqlite` содержит только эти 100 записей и нужна существующему скрипту расшифровки.

Первые 500 позиций обрабатываются на Aeza. Позиции 501–600 обрабатываются на основном ПК. Этот репозиторий предназначен для ноутбука с Windows 10, Ryzen 3 3500 и 8 ГБ RAM.

## Запуск на Windows 10

Установить Python 3.11 или 3.12 для Windows с опцией добавления в PATH. В PowerShell:

```powershell
git clone https://github.com/ReFleX9/stag.git
cd stag
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install faster-whisper==1.2.1 av==14.2.0
.\.venv\Scripts\python.exe -u .\transcribe_voices.py --root .\STAG_SECOND_CHANNEL --device cpu --cpu-threads 4
```

Модель `small` будет загружена при первом запуске. Сохранённые JSON лежат в `STAG_SECOND_CHANNEL/knowledge/transcripts/`. Повторный запуск той же последней команды пропускает готовые файлы. Перед повтором дождаться завершения прежнего процесса. Ноутбук держать подключённым к сети и отключить сон на время обработки.

Прогресс: вывод PowerShell и число файлов `Get-ChildItem .\STAG_SECOND_CHANNEL\knowledge\transcripts\*.json | Measure-Object`. Цель — 100 файлов. После окончания проверьте ошибки в `STAG_SECOND_CHANNEL/knowledge/transcription_errors.log`, если файл появился.

Для продолжения разбора в Codex: работать с `batch_601_700.json` и расшифровками, затем объединить их с результатами первых 600 позиций по `message_id` и `voice_file`. Текстовое сообщение или изображение из полного экспорта здесь отсутствуют; при анализе использовать оригинальный проект.
