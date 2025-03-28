# Обработка банковских PDF-выписок и генерация файла для загрузки в iiko
![Logo](https://febrein.top/apisyrve/icon.png)

Проект предназначен для автоматизации процесса обработки банковских выписок в формате PDF и подготовки данных в формате **1CClientBankExchange**, который поддерживается системой **iiko**.

---

## 📌 Описание проекта

Приложение парсит выписки из банковских PDF-файлов (например, из ПриватБанка и Таскомбанка), собирает информацию о транзакциях и автоматически формирует файл формата **1CClientBankExchange** для загрузки в систему **iiko**.

---

## 🔧 Используемые технологии

- **Python 3.x**
- Библиотека для работы с PDF: [`pdfplumber`](https://github.com/jsvine/pdfplumber)
- Формат выходных данных: **1CClientBankExchange**
- IDE разработки: любая (например, PyCharm, VSCode)

---

## 📁 Структура проекта

```plaintext
project-root/
├── main.py                        # Основной исполняемый скрипт
├── requirements.txt               # Зависимости проекта
├── models/
│   └── transaction.py             # Модель данных транзакции
├── parsers/
│   ├── base_parser.py             # Базовый класс парсера
│   ├── privatbank_pdf_parser.py   # Парсер PDF ПриватБанка
│   └── taskombank_pdf_parser.py   # Парсер PDF Таскомбанка
├── generators/
│   └── iiko_1c_file_generator.py  # Генератор файла 1C для iiko
└── services/
    └── bank_statement_service.py  # Сервис обработки выписок
```
## Документация Айко

[Documentation](https://ru.iiko.help/articles/#!iikooffice-9-1/topic-410/a/h2_2063664150)


## Доп инфо

Данный скрипт написанный на питоне призван для парсинга ПДФ файла банка.

В данный момент есть только два банка Украины.

Помимо этого в документации айко не указано инфо о том как верно генерировать текстовый файл

Именно поэтому я делаю ремарку на то что бы вы не спотыкались об ошибки

## Пример тхт файла 
```plaintext
1CClientBankExchange
ВерсияФормата=1.02
Кодировка=Windows
Отправитель=Бухгалтерия предприятия, редакция 3.0
Получатель=
ДатаСоздания=09.12.2015
ВремяСоздания=10:33:20
ДатаНачала=09.12.2015
ДатаКонца=09.12.2015
РасчСчет=40702810300180001774
Документ=Платежное поручение
Документ=Платежное требование
СекцияДокумент=Платежное поручение
Номер=105
Дата=09.12.2015
Сумма=12354.00
ПлательщикСчет=40702810300180001774
ПлательщикИНН=7719617469 ОАО Крокус
ПлательщикИНН=7719617469
Плательщик1=ОАО Крокус
ПлательщикРасчСчет=40702810300180001774
ПлательщикБанк1=АО ОТП БАНК
ПлательщикБанк2=Г. МОСКВА
ПлательщикБИК=044525311
ПлательщикКорсчет=30101810000000000311
ПолучательСчет=40702810123111111114
Получатель=ИНН 7701325469 ОАО Прогресс Парк
ПолучательИНН=7701325469
Получатель1=ОАО Прогресс Парк
ПолучательРасчСчет=40702810123111111114
ПолучательБанк1=ОАО БАНК ПЕТРОКОММЕРЦ
ПолучательБанк2=Г. МОСКВА
ПолучательБИК=044525352
ПолучательКорсчет=30101810700000000352
ВидОплаты=01
ПлательщикКПП=771901001
Очередность=5
НазначениеПлатежа=Оплата по договору. Сумма 12354-00 без налога (НДС)
НазначениеПлатежа1=Оплата по договору. Сумма 12354-00 без налога (НДС)
КонецДокумента
КонецФайла
```

Если мы желаем все транзакции хранить в одном файле тогда мы каждую транзакцию ограждаем в начале 1CClientBankExchange а в конце КонецДокумента 
Так же обратите внимание что синтаксис зависит от версии айко, обычно в ошибках явно указывается что необходимо исправить, так же это логируется в логах бек офиса

