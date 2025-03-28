# main.py

from onik.project.services.bank_statement_service import BankStatementService
from onik.project.parsers.privatbank_pdf_parser import PrivatBankPdfParser
from onik.project.parsers.taskombank_pdf_parser import TaskombankPdfParser


# def main():
#    service = BankStatementService()
    # Регистрируем парсеры
#    service.register_parser("privat_pdf", PrivatBankPdfParser())
#    service.register_parser("taskombank_pdf", TaskombankPdfParser())

    # 1) Парсим файл ПриватБанка
#    pdf_file_path_priv = "privat.pdf"
#    iiko_text_priv = service.process_file(pdf_file_path_priv, "privat_pdf")
    # Сохраняем результат в первый txt
#    with open("out_for_iiko_privat.txt", "w", encoding="utf-8") as f1:
#        f1.write(iiko_text_priv)

    # 2) Парсим файл ТАСКОМБАНКА
#    pdf_file_path_taskom = "taskombank.pdf"
#    iiko_text_taskom = service.process_file(pdf_file_path_taskom, "taskombank_pdf")
    # Сохраняем результат во второй txt
#    with open("out_for_iiko_taskombank.txt", "w", encoding="utf-8") as f2:
#        f2.write(iiko_text_taskom)

#    print("Два файла успешно сформированы и готовы к загрузке в бек.")


#if __name__ == "__main__":
#    main()
def main():
    service = BankStatementService()
    service.register_parser("privat_pdf", PrivatBankPdfParser())
    service.register_parser("taskombank_pdf", TaskombankPdfParser())

    # Получаем текст для каждого файла
    privat_text = service.process_file("privat.pdf", "privat_pdf")
    taskombank_text = service.process_file("taskombank.pdf", "taskombank_pdf")

    # Если каждый блок заканчивается "КонецФайла", удалим его из первого блока
    if privat_text.rstrip().endswith("КонецФайла"):
        privat_text = privat_text.rstrip()[:-len("КонецФайла")].rstrip()

    # Объединим оба результата и добавим один финальный "КонецФайла"
    combined_text = privat_text + "\n" + taskombank_text
    # Если последний блок уже содержит "КонецФайла", оставляем как есть,
    # иначе можно добавить его:
    if not combined_text.rstrip().endswith("КонецФайла"):
        combined_text += "\nКонецФайла"

    # Сохраняем результат в один файл
    with open("out_for_syrve_combined.txt", "w") as f:
        f.write(combined_text)

    print("Объединённый файл успешно сформирован.")


if __name__ == "__main__":
    main()
