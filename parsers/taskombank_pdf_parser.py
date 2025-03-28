import pdfplumber
import re
from typing import List, Optional
from datetime import datetime

from onik.project.parsers.base_parser import BaseBankStatementParser
from onik.project.models.transaction import Transaction

class TaskombankPdfParser(BaseBankStatementParser):
    """
    Парсер PDF-выписок ТАСКОМБАНКА.
    1) Извлекает "наши" реквизиты (юрлицо, счёт, ИНН) из шапки первой страницы.
    2) Обрабатывает таблицу, где, условно:
       - col 0: Дата опер. (с временем)
       - col 1: Дебет
       - col 2: Кредит
       - col 3: Реквізити кореспондента
       - col 4: Призначення платежу
    3) Определяет расход/приход по заполненной колонке Дебет/Кредит.
    4) Склеивает многострочные ячейки реквизитов контрагента.
    """

    def __init__(self):
        # Данные нашей компании (заполняются из шапки)
        self.our_company_name: Optional[str] = None
        self.our_company_inn: Optional[str] = None
        self.our_company_account: Optional[str] = None

        self.our_bank_name: Optional[str] = None
        self.our_bank_id: Optional[str] = None

    def parse(self, file_path: str) -> List[Transaction]:
        transactions: List[Transaction] = []
        with pdfplumber.open(file_path) as pdf:
            # 1) Считываем "шапку" (первая страница)
            if pdf.pages:
                self._extract_our_company_data(pdf.pages[0])

            # 2) Проходим по всем страницам, извлекаем таблицы
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue

                for table in tables:
                    if len(table) < 2:
                        continue

                    header = table[0]
                    if len(header) < 5:
                        continue

                    data_rows = table[1:]
                    for row in data_rows:
                        if len(row) < 5:
                            continue

                        date_str = (row[0] or "").strip()
                        debit_str = (row[1] or "").replace(",", ".").replace(" ", "")
                        credit_str = (row[2] or "").replace(",", ".").replace(" ", "")

                        corr_info_raw = (row[3] or "")
                        payment_details = (row[4] or "").strip()

                        # Парсим дату
                        op_date = self._parse_date(date_str)

                        # Определяем сумму (если в дебете > 0 => расход, если в кредите => приход)
                        amount = 0.0
                        if debit_str:
                            try:
                                amount = -float(debit_str)
                            except ValueError:
                                amount = 0.0
                        elif credit_str:
                            try:
                                amount = float(credit_str)
                            except ValueError:
                                amount = 0.0

                        # Склеиваем ячейки реквизитов контрагента
                        lines = corr_info_raw.splitlines()
                        corr_info = " ".join(line.strip() for line in lines)
                        corr_info = re.sub(r"\s+", " ", corr_info).strip()

                        # Дополнительно можно искать "Номер док-та: XXX"
                        doc_number = self._extract_doc_number(corr_info + " " + payment_details)

                        # Ищем INN, счёт
                        contragent_inn = self._extract_inn(corr_info)
                        contragent_account = self._extract_account(corr_info)

                        # Название контрагента
                        contragent_name = self._cleanup_name(corr_info, contragent_inn, contragent_account)

                        # Формируем Transaction
                        transaction = self._build_transaction(
                            doc_number=doc_number,
                            op_date=op_date,
                            amount=amount,
                            payment_details=payment_details,
                            contragent_name=contragent_name,
                            contragent_inn=contragent_inn,
                            contragent_account=contragent_account
                        )
                        transactions.append(transaction)

        return transactions

    # ---------------- Вспомогательные методы ----------------

    def _extract_our_company_data(self, page) -> None:
        """
        Считываем текст шапки (первая страница) и ищем:
          - "ТОВ 'РЕВІ-НАЙТ', ЄДРПОУ 45619342"
          - "Виписка по рахунку N UA30 ..."
          - "АТ 'ТАСКОМБАНК' Київ, код ID НБУ 339500"
        """
        text = page.extract_text() or ""
        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()

            # Пример: АТ "ТАСКОМБАНК" ... код ID НБУ 339500
            match_bank = re.search(r'АТ\s+"ТАСКОМБАНК".*код\s+ID\s+НБУ\s+(\d+)', line_str, re.IGNORECASE)
            if match_bank:
                self.our_bank_name = 'АТ "ТАСКОМБАНК"'
                self.our_bank_id = match_bank.group(1)

            # ТОВ "РЕВІ-НАЙТ", ЄДРПОУ 45619342
            match_company = re.search(r'ТОВ\s+"([^"]+)",\s*ЄДРПОУ\s+(\d+)', line_str, re.IGNORECASE)
            if match_company:
                self.our_company_name = match_company.group(1).strip()
                self.our_company_inn = match_company.group(2).strip()

            # "Виписка по рахунку N UA30..."
            match_acc = re.search(r'Виписка\s+по\s+рахунку\s+N\s+(UA[\d\s]+)', line_str, re.IGNORECASE)
            if match_acc:
                raw_acc = match_acc.group(1).replace(" ", "")
                self.our_company_account = raw_acc

    def _parse_date(self, date_str: str) -> datetime:
        date_str = date_str.replace("\n", " ")
        for fmt in ["%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"]:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return datetime.now()

    def _extract_doc_number(self, text: str) -> str:
        match = re.search(r'Номер\s+док-та:\s*(\S+)', text)
        if match:
            return match.group(1)
        return "UNKNOWN"

    def _extract_inn(self, text: str) -> str:
        """
        Ищем "ЄДРПОУ: 12345678" либо 8-10 цифр подряд.
        """
        match = re.search(r'ЄДРПОУ:\s*(\d+)', text)
        if match:
            return match.group(1)
        match_digits = re.search(r"\b\d{8,10}\b", text)
        if match_digits:
            return match_digits.group(0)
        return ""

    def _extract_account(self, text: str) -> str:
        """
        Ищем "Рахунок: UA..." или просто UA.., убираем пробелы.
        """
        match = re.search(r'Рахунок:\s*(UA[\w\d]+)', text)
        if match:
            return match.group(1).replace(" ", "")
        match_ua = re.search(r"\b(UA\d{2,})\b", text)
        if match_ua:
            return match_ua.group(1)
        return ""

    def _cleanup_name(self, text: str, inn: str, account: str) -> str:
        """
        Удаляем "ЄДРПОУ:...", сам inn, "Рахунок:...", сам account.
        """
        cleaned = text
        cleaned = re.sub(r"ЄДРПОУ:\s*\d+", "", cleaned)
        if inn:
            cleaned = cleaned.replace(inn, "")
        if account:
            cleaned = cleaned.replace(account, "")
        cleaned = re.sub(r"Рахунок:\s*UA[\w\d]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _build_transaction(
        self,
        doc_number: str,
        op_date: datetime,
        amount: float,
        payment_details: str,
        contragent_name: str,
        contragent_inn: str,
        contragent_account: str
    ) -> Transaction:
        """
        Если amount < 0 => мы платим => payer_inn="1", recipient_inn=contragent_inn
        Если amount > 0 => нам платят => payer_inn=contragent_inn, recipient_inn="1"
        """
        our_name = self.our_company_name or "OUR_COMPANY"
        our_account = self.our_company_account or ""

        if amount < 0:
            # Расход
            payer_inn = "1"
            payer_name = our_name
            payer_account = our_account

            recipient_inn = contragent_inn
            recipient_name = contragent_name
            recipient_account = contragent_account

            date_outcome = op_date.date()
            date_income = None
        else:
            # Приход
            payer_inn = contragent_inn
            payer_name = contragent_name
            payer_account = contragent_account

            recipient_inn = "1"
            recipient_name = our_name
            recipient_account = our_account

            date_outcome = None
            date_income = op_date.date()

        return Transaction(
            number=doc_number,
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
