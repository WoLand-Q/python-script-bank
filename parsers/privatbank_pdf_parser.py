import pdfplumber
import re
from typing import List, Optional
from datetime import datetime

from onik.project.parsers.base_parser import BaseBankStatementParser
from onik.project.models.transaction import Transaction

class PrivatBankPdfParser(BaseBankStatementParser):
    """
    Парсер PDF-выписок ПриватБанк.
    1) Извлекает реквизиты из шапки (юрлицо, счёт, ИНН).
    2) Обрабатывает таблицу, где первая строка (row[0]) - остатки,
       row[1] и row[2] - "двухэтажный" заголовок,
       row[3:] - строки данных о транзакциях.
    3) Для каждой строки данных создаёт объект Transaction,
       определяя, кто плательщик, а кто получатель (если сумма < 0, расход).
    4) Специально "склеиваем" ячейки контрагента, чтобы не было переноса
       внутри `ПолучательРасчСчет=` и т.д.
    """

    def __init__(self):
        self.our_company_name: Optional[str] = None
        self.our_company_inn: Optional[str] = None
        self.our_company_account: Optional[str] = None
        self.our_bank_name: Optional[str] = None
        self.our_bank_edrpou: Optional[str] = None
        self.our_bank_branch: Optional[str] = None

    def parse(self, file_path: str) -> List[Transaction]:
        transactions: List[Transaction] = []
        with pdfplumber.open(file_path) as pdf:
            # 1) Считываем "шапку" (первая страница)
            if pdf.pages:
                self._extract_our_company_data(pdf.pages[0])

            # 2) Проходим по всем страницам, ищем таблицы
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue

                for table in tables:
                    # Нужно минимум 4 строки: [0] - остатки, [1,2] - заголовок, [3..] - данные
                    if len(table) < 4:
                        continue

                    # row[1], row[2] - двухэтажный заголовок
                    header1 = table[1]
                    header2 = table[2]
                    if len(header1) < 7 or len(header2) < 7:
                        continue

                    # row[3..] - данные
                    data_rows = table[3:]
                    for row_data in data_rows:
                        if len(row_data) < 7:
                            continue

                        # 0: Номер документа
                        doc_number = (row_data[0] or "").strip()
                        # 1: Дата + время
                        date_str = (row_data[1] or "").strip()
                        # 2: Сумма
                        amount_str = (row_data[2] or "").replace(",", ".").replace(" ", "")
                        # 3: Назначение платежа
                        payment_details = (row_data[3] or "").strip()

                        # Парсим дату/время
                        op_date = self._parse_date(date_str)

                        # Парсим сумму
                        try:
                            amount = float(amount_str)
                        except ValueError:
                            amount = 0.0

                        # 5: часть реквизитов контрагента
                        part1 = (row_data[5] or "").splitlines()
                        # 6: остальная часть реквизитов
                        part2 = (row_data[6] or "").splitlines()
                        # Склеиваем всё в одну строку
                        contragent_full = " ".join(part1 + part2).strip()
                        contragent_full = re.sub(r"\s+", " ", contragent_full)

                        # Ищем ИНН, счёт
                        contragent_inn = self._find_inn(contragent_full)
                        contragent_account = self._find_account(contragent_full)
                        # "Чистое" название контрагента (убираем INN и счёт из строки)
                        contragent_name = self._clean_name(contragent_full, contragent_inn, contragent_account)

                        # Собираем Transaction
                        transaction = self._build_transaction(
                            number=doc_number,
                            op_date=op_date,
                            amount=amount,
                            payment_details=payment_details,
                            contragent_name=contragent_name.strip(),
                            contragent_inn=contragent_inn,
                            contragent_account=contragent_account
                        )

                        # (Дополнительно) Распределяем ИНН/счёт в зависимости от знака суммы
                        if amount < 0:  # расход
                            transaction.recipient_inn = contragent_inn
                            transaction.recipient_account = contragent_account
                        else:  # приход
                            transaction.payer_inn = contragent_inn
                            transaction.payer_account = contragent_account

                        transactions.append(transaction)

        return transactions

    # ----------------- Вспомогательные методы --------------------

    def _extract_our_company_data(self, page) -> None:
        text = page.extract_text() or ""
        for line_stripped in text.split("\n"):
            line_stripped = line_stripped.strip()

            # Пример поиска "АТ КБ "ПРИВАТБАНК", ЄДРПОУ 14360570"
            match_bank = re.search(r'(АТ\s+КБ\s+"[^"]+"),?\s*ЄДРПОУ\s+(\d+)', line_stripped)
            if match_bank:
                self.our_bank_name = match_bank.group(1)
                self.our_bank_edrpou = match_bank.group(2)

            # Пример: "Клієнт БРУСКЕРДО ТОВ, ЄДРПОУ 37762243"
            match_company = re.search(r"Клієнт\s+(.+?),\s+ЄДРПОУ\s+(\d+)", line_stripped)
            if match_company:
                self.our_company_name = match_company.group(1)
                self.our_company_inn = match_company.group(2)

            # Пример: "Поточний рахунок №UA4030..."
            match_account = re.search(r"Поточний рахунок\s+№(\w+)", line_stripped)
            if match_account:
                self.our_company_account = match_account.group(1)

    def _parse_date(self, date_str: str) -> datetime:
        date_str = date_str.replace("\n", " ")
        formats = ["%d.%m.%Y %H:%M", "%d.%m.%Y", "%d/%m/%Y %H:%M"]
        for f in formats:
            try:
                return datetime.strptime(date_str.strip(), f)
            except ValueError:
                continue
        return datetime.now()

    def _find_inn(self, text: str) -> str:
        """Ищем "ЄДРПОУ: 12345678" или 8–10 цифр подряд."""
        match = re.search(r"ЄДРПОУ:\s*(\d+)", text)
        if match:
            return match.group(1)
        # Или любой 8–10-значный кусок цифр
        match_digits = re.search(r"\b\d{8,10}\b", text)
        if match_digits:
            return match_digits.group(0)
        return ""

    def _find_account(self, text: str) -> str:
        """Ищем "Рахунок: UA..." или просто UA.. (без пробелов)."""
        match = re.search(r"Рахунок:\s*(UA[\w\d]+)", text)
        if match:
            return match.group(1).replace(" ", "")
        match_ua = re.search(r"\b(UA\d{2,})\b", text)
        if match_ua:
            return match_ua.group(1)
        return ""

    def _clean_name(self, text: str, inn: str, account: str) -> str:
        """Убираем из текста упоминание 'ЄДРПОУ: ...' и 'Рахунок: ...'."""
        cleaned = re.sub(r"ЄДРПОУ:\s*\d+", "", text)
        if inn:
            cleaned = cleaned.replace(inn, "")
        cleaned = re.sub(r"Рахунок:\s*UA[\w\d]+", "", cleaned)
        if account:
            cleaned = cleaned.replace(account, "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _build_transaction(
        self,
        number: str,
        op_date: datetime,
        amount: float,
        payment_details: str,
        contragent_name: str,
        contragent_inn: str,
        contragent_account: str
    ) -> Transaction:
        """
        Если сумма < 0 => наша фирма плательщик (payer_inn="1"), контрагент — получатель (его реальный INN).
        Если сумма > 0 => контрагент плательщик (contragent_inn), наша фирма — получатель (inn="1").
        """
        our_name = self.our_company_name or "OUR_COMPANY"
        our_account = self.our_company_account or ""

        if amount < 0:
            # Расход: мы платим => payer_inn="1", recipient_inn=contragent_inn
            payer_inn = "1"
            payer_name = our_name
            payer_account = our_account

            recipient_inn = contragent_inn
            recipient_name = contragent_name
            recipient_account = contragent_account

            date_outcome = op_date.date()
            date_income = None
        else:
            # Приход: нам платят => payer_inn=contragent_inn, recipient_inn="1"
            payer_inn = contragent_inn
            payer_name = contragent_name
            payer_account = contragent_account

            recipient_inn = "1"
            recipient_name = our_name
            recipient_account = our_account

            date_outcome = None
            date_income = op_date.date()

        return Transaction(
            number=number,
            date=op_date.date(),
            amount=amount,
            payer_inn=payer_inn,
            payer_name=payer_name,
            payer_account=payer_account,
            recipient_inn=recipient_inn,
            recipient_name=recipient_name,
            recipient_account=recipient_account,
            payment_details=payment_details.strip(),
            date_income=date_income,
            date_outcome=date_outcome,
        )
