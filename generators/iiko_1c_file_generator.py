# generators/iiko_1c_file_generator.py

from typing import List
from datetime import datetime
from onik.project.models.transaction import Transaction

from typing import List
from datetime import datetime
from onik.project.models.transaction import Transaction

class Iiko1CFileGenerator:
    """
    Генерирует итоговый текст в формате 1CClientBankExchange,
    который потом можно загрузить в iiko.

    Для каждой транзакции формируется отдельный блок,
    заканчивается "КонецДокумента".
    """

    def generate_file_content(self, transactions: List[Transaction]) -> str:
        blocks = []
        now_date = datetime.now().strftime('%d.%m.%Y')
        now_time = datetime.now().strftime('%H:%M:%S')

        for t in transactions:
            block_lines = []

            # Заголовок файла (по требованиям 1C/iiko)
            block_lines.append("1CClientBankExchange")
            block_lines.append("ВерсияФормата=1.01")
            block_lines.append("Кодировка=Windows")
            block_lines.append("Отправитель=Python Script")
            block_lines.append("Получатель=")
            block_lines.append(f"ДатаСоздания={now_date}")
            block_lines.append(f"ВремяСоздания={now_time}")
            block_lines.append(f"ДатаНачала={now_date}")
            block_lines.append(f"ДатаКонца={now_date}")
            block_lines.append(f"РасчСчет={t.payer_account or ''}")

            # Начало документа
            block_lines.append("Документ=Платежное поручение")
            block_lines.append("СекцияДокумент=Платежное поручение")

            block_lines.append(f"Номер={t.number}")
            block_lines.append(f"Дата={t.date.strftime('%d.%m.%Y')}")

            # Сумма всегда положительная для iiko
            block_lines.append(f"Сумма={abs(t.amount):.2f}")

            # --- Плательщик ---
            if t.payer_inn:
                block_lines.append(f"ПлательщикИНН={t.payer_inn}")
            else:
                block_lines.append("ПлательщикИНН=")
            block_lines.append(f"Плательщик1={t.payer_name or ''}")

            if t.payer_account:
                block_lines.append(f"ПлательщикРасчСчет={t.payer_account}")
            else:
                block_lines.append("ПлательщикРасчСчет=")

            # --- Получатель ---
            if t.recipient_inn:
                block_lines.append(f"ПолучательИНН={t.recipient_inn}")
            else:
                block_lines.append("ПолучательИНН=")
            block_lines.append(f"Получатель1={t.recipient_name or ''}")

            if t.recipient_account:
                block_lines.append(f"ПолучательРасчСчет={t.recipient_account}")
            else:
                block_lines.append("ПолучательРасчСчет=")

            # Назначение
            block_lines.append(f"НазначениеПлатежа={t.payment_details}")
            block_lines.append(f"НазначениеПлатежа1={t.payment_details}")

            # Даты поступления/списания
            if t.date_income:
                block_lines.append(f"ДатаПоступило={t.date_income.strftime('%d.%m.%Y')}")
            else:
                block_lines.append("ДатаПоступило=")

            if t.date_outcome:
                block_lines.append(f"ДатаСписано={t.date_outcome.strftime('%d.%m.%Y')}")
            else:
                block_lines.append("ДатаСписано=")

            block_lines.append("КонецДокумента")
            blocks.append("\n".join(block_lines))

        final_text = "\n".join(blocks)
        return final_text

