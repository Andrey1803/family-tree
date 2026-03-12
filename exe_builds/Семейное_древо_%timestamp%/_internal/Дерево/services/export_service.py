# -*- coding: utf-8 -*-
"""
Сервис экспорта данных.
Поддерживает экспорт в PDF, CSV, простой текст.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ExportService:
    """Сервис для экспорта данных дерева."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Инициализация сервиса.

        Args:
            data_dir: Директория для данных. Если None, используется текущая.
        """
        self.data_dir = Path(data_dir) if data_dir else Path.cwd()

    def export_to_pdf(self, tree_data: Dict[str, Any], output_path: str, username: str) -> tuple[bool, Optional[str]]:
        """
        Экспортирует дерево в PDF с графическим представлением.

        Args:
            tree_data: Данные дерева.
            output_path: Путь для выходного файла.
            username: Имя пользователя.

        Returns:
            (success, error_message): Кортеж с результатом и сообщением об ошибке.
        """
        try:
            from export_pdf import export_to_pdf as pdf_export
            result = pdf_export(tree_data, output_path, username)
            if result:
                logger.info(f"PDF экспортирован: {output_path}")
                return True, None
            return False, "Экспорт в PDF вернул пустой результат"
        except ImportError:
            return False, "Модуль экспорта PDF недоступен"
        except Exception as e:
            logger.error(f"Ошибка экспорта в PDF: {e}")
            return False, str(e)

    def export_simple_pdf(self, tree_data: Dict[str, Any], output_path: str) -> tuple[bool, Optional[str]]:
        """
        Экспортирует дерево в простой текстовый PDF.

        Args:
            tree_data: Данные дерева.
            output_path: Путь для выходного файла.

        Returns:
            (success, error_message): Кортеж с результатом и сообщением об ошибке.
        """
        try:
            from export_pdf import export_simple_pdf as simple_export
            result = simple_export(tree_data, output_path)
            if result:
                logger.info(f"Простой PDF экспортирован: {output_path}")
                return True, None
            return False, "Простой экспорт PDF вернул пустой результат"
        except ImportError:
            return False, "Модуль экспорта PDF недоступен"
        except Exception as e:
            logger.error(f"Ошибка простого экспорта в PDF: {e}")
            return False, str(e)

    def export_to_csv(self, tree_data: Dict[str, Any], output_path: str) -> tuple[bool, Optional[str]]:
        """
        Экспортирует персоны в CSV.

        Args:
            tree_data: Данные дерева.
            output_path: Путь для выходного файла.

        Returns:
            (success, error_message): Кортеж с результатом и сообщением об ошибке.
        """
        try:
            import csv
            persons = tree_data.get("persons", {})

            if not persons:
                return False, "Нет данных для экспорта"

            fieldnames = [
                "id", "name", "surname", "patronymic", "gender",
                "birth_date", "death_date", "is_deceased",
                "birth_place", "occupation", "education", "notes"
            ]

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for pid, person in persons.items():
                    row = {k: person.get(k, "") for k in fieldnames}
                    row["id"] = pid
                    writer.writerow(row)

            logger.info(f"CSV экспортирован: {output_path}")
            return True, None

        except Exception as e:
            logger.error(f"Ошибка экспорта в CSV: {e}")
            return False, str(e)

    def import_from_csv(self, input_path: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Импортирует персоны из CSV.

        Args:
            input_path: Путь к CSV файлу.

        Returns:
            (success, persons_dict, error_message): Кортеж с результатом, данными и ошибкой.
        """
        try:
            import csv
            persons = {}

            with open(input_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, start=1):
                    person_id = row.get("id") or str(i)
                    persons[person_id] = {
                        "name": row.get("name", ""),
                        "surname": row.get("surname", ""),
                        "patronymic": row.get("patronymic", ""),
                        "gender": row.get("gender", ""),
                        "birth_date": row.get("birth_date", ""),
                        "death_date": row.get("death_date", ""),
                        "is_deceased": row.get("is_deceased", "").lower() in ("true", "1", "да"),
                        "birth_place": row.get("birth_place", ""),
                        "occupation": row.get("occupation", ""),
                        "education": row.get("education", ""),
                        "notes": row.get("notes", ""),
                        "parents": [],
                        "children": [],
                        "spouse_ids": [],
                    }

            logger.info(f"CSV импортирован: {len(persons)} персон")
            return True, persons, None

        except Exception as e:
            logger.error(f"Ошибка импорта из CSV: {e}")
            return False, None, str(e)

    def export_to_text(self, tree_data: Dict[str, Any], output_path: str) -> tuple[bool, Optional[str]]:
        """
        Экспортирует дерево в текстовый файл.

        Args:
            tree_data: Данные дерева.
            output_path: Путь для выходного файла.

        Returns:
            (success, error_message): Кортеж с результатом и сообщением об ошибке.
        """
        try:
            persons = tree_data.get("persons", {})
            marriages = tree_data.get("marriages", [])

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=== Семейное древо ===\n\n")
                f.write(f"Персон: {len(persons)}\n")
                f.write(f"Браков: {len(marriages)}\n\n")

                f.write("=== Персоны ===\n")
                for pid, p in persons.items():
                    name = p.get("surname", "") + " " + p.get("name", "")
                    if p.get("patronymic"):
                        name += " " + p.get("patronymic", "")
                    f.write(f"[{pid}] {name}")
                    if p.get("gender"):
                        f.write(f" ({p.get('gender')})")
                    if p.get("birth_date"):
                        f.write(f", р. {p.get('birth_date')}")
                    if p.get("death_date"):
                        f.write(f", ум. {p.get('death_date')}")
                    f.write("\n")

                f.write("\n=== Браки ===\n")
                for m in marriages:
                    f.write(f"{m[0]} <-> {m[1]}\n")

            logger.info(f"Текстовый файл экспортирован: {output_path}")
            return True, None

        except Exception as e:
            logger.error(f"Ошибка экспорта в текст: {e}")
            return False, str(e)
