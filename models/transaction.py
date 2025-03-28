# models/transaction.py

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Transaction:
    """
    Унифицированная модель данных о транзакции,
    которую возвращают все парсеры.
    """
    number: str  # Номер документа
    date: date  # Дата документа (или datetime, если нужно время)
    amount: float  # Сумма платежа
    payer_inn: Optional[str]  # ИНН плательщика
    payer_name: str  # Название/ФИО плательщика
    payer_account: Optional[str]  # Расчётный счёт плательщика

    recipient_inn: Optional[str]  # ИНН получателя
    recipient_name: str  # Название/ФИО получателя
    recipient_account: Optional[str]  # Расчётный счёт получателя

    payment_details: str  # Назначение платежа
    date_income: Optional[date]  # Дата поступления (DateПоступило)
    date_outcome: Optional[date]  # Дата списания (DateСписано)

    # Дополнительные поля по необходимости, например BIC, корр.счёт и т.д.
    # Можно дополнять, когда расширяем функционал.
