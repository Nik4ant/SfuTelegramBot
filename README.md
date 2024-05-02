# SfuTelegramBot
To-Do: описание

# Инструкции
## Как начать
0) Установлен Python версии 3.11.x
1) Установить [pdm](https://github.com/pdm-project/pdm?tab=readme-ov-file#installation)
выполнив команду в powershell (для Windows, если пользуетесь Linux'ом, то вряд ли вам нужна эта инструкция...): 
```
(Invoke-WebRequest -Uri https://pdm-project.org/install-pdm.py -UseBasicParsing).Content | python -
```
или
```
pip install pdm
```
2) *Скачать* проект:
   - Зайти в желаемую папку и выполнить команду: ```git clone https://github.com/Nik4ant/SfuTelegramBot.git```
   - Затем: `cd SfuTelegramBot`
   - Внутри проекта: `pdm install`
3) Создать файл `.env` и записать туда: 
```
TELEGRAM_TOKEN={{token}}
```
Где вместо `{{token}}` будет секретный токен от Телеграм бота, чтобы его получить напишите (просто добавить его в репозиторий нельзя)

4) Готово. Теперь запустите `pdm run start` и всё должно работать. (флаг --support_enabled для запуска бота поддержки)
## i18n
Для генерации файлов локали в корневой папке проекта:
`python "/path/to/i18n/tool/in/python/pygettext.py" -d base -o locales/base.pot src/`

## Как пользоваться
В проекте используется специальная утилита [pdm](https://pdm-project.org/latest/), основные команды, которые надо знать:
- `pdm run start`: запускает проект
- `pdm run format`: форматирует код проекта, чтобы соблюдать стилистику и всё такое...
- `pdm run lint`: сканирует код проекта, чтобы найти какие-либо стилистические, типовые (т.е. проверяет типы) и прочие ошибки
- Если нужно добавить какую-то стороннюю библиотеку, то вместо привычного `pip install` нужно использовать: `pdm add {{имя_пакета}}`
