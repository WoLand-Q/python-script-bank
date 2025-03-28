# services/bank_statement_service.py

from typing import Optional
from onik.project.parsers.base_parser import BaseBankStatementParser
from onik.project.parsers.privatbank_pdf_parser import PrivatBankPdfParser
from onik.project.generators.iiko_1c_file_generator import Iiko1CFileGenerator
from onik.project.models.transaction import Transaction
import os


class BankStatementService:
    """
    Основной сервис, который:
    1) Выбирает нужный парсер.
    2) Парсит файл.
    3) Генерирует выходной текст.
    """

    def __init__(self):
        # Можно хранить доступные парсеры в виде словаря
        # или использовать фабрику.
        self.parsers_map = {
            # 'pdf_privat': PrivatBankPdfParser(),
            # '1c_mono': Monobank1CParser()
            # ...
        }
        self.file_generator = Iiko1CFileGenerator()

    def register_parser(self, key: str, parser: BaseBankStatementParser):
        """
        Регистрируем парсер под определённым ключом (например, 'privat_pdf'),
        чтобы дальше знать, как выбирать нужный парсер.
        """
        self.parsers_map[key] = parser

    def process_file(self, file_path: str, parser_key: str) -> str:
        """
        Высокоуровневая функция, которую вызываем из кода бота/веб-сервиса/CLI:
          1) Находит нужный парсер по ключу.
          2) Парсит файл -> список Transaction.
          3) Генерирует текст в формате 1CClientBankExchange.
          4) Возвращает этот текст, чтобы можно было сохранить/отправить.
        """
        if parser_key not in self.parsers_map:
            raise ValueError(f"Не найден парсер с ключом '{parser_key}'")

        parser = self.parsers_map[parser_key]
        transactions = parser.parse(file_path)

        return self.file_generator.generate_file_content(transactions)
