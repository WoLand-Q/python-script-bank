# parsers/base_parser.py

from abc import ABC, abstractmethod
from typing import List
from onik.project.models.transaction import Transaction

class BaseBankStatementParser(ABC):
    """
    Абстрактный базовый класс для всех парсеров банковских выписок.
    """

    @abstractmethod
    def parse(self, file_path: str) -> List[Transaction]:
        """
        Парсит входной файл и возвращает список транзакций.
        """
        pass
