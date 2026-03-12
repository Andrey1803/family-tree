# -*- coding: utf-8 -*-
"""
Экспорт семейного дерева в PDF.

Создаёт красивый документ с:
- Древом предков
- Списком всех персон
- Статистикой
"""

import io
import os
from datetime import datetime

# Проверяем доступность reportlab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def export_to_pdf(model, filename=None):
    """
    Экспортирует семейное дерево в PDF (упрощённая версия).
    """
    if not PDF_AVAILABLE:
        return None
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"family_tree_{timestamp}.pdf"
    
    try:
        # Создаём простой PDF
        c = canvas.Canvas(filename, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        # Заголовок
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height - 2*cm, "Family Tree")
        
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 2.5*cm, f"Exported: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # Статистика
        persons = list(model.get_all_persons().values())
        male_count = sum(1 for p in persons if p.gender == 'Мужской')
        female_count = sum(1 for p in persons if p.gender == 'Женский')
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, height - 4*cm, f"Total: {len(persons)} persons")
        c.drawString(2*cm, height - 4.5*cm, f"Males: {male_count}")
        c.drawString(2*cm, height - 5*cm, f"Females: {female_count}")
        
        # Список персон (транслитерация для совместимости)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, height - 6*cm, "All Persons:")
        
        y = height - 6.5*cm
        line_height = 0.5*cm
        
        for i, person in enumerate(sorted(persons, key=lambda p: p.birth_date or '9999'), 1):
            if y < 2*cm:  # Новая страница
                c.showPage()
                y = height - 2*cm
            
            # Транслитерация или латиница
            name_latin = transliterate(person.surname) + " " + transliterate(person.name)
            if person.patronymic:
                name_latin += " " + transliterate(person.patronymic)
            
            birth = person.birth_date or "?"
            death = person.death_date if person.is_deceased else "—"
            gender = "M" if person.gender == "Мужской" else "F"
            
            c.setFont("Helvetica", 10)
            c.drawString(2*cm, y, f"{i}. {name_latin} ({gender}) | b. {birth} | d. {death}")
            y -= line_height
        
        c.save()
        return filename
        
    except Exception as e:
        print(f"Ошибка экспорта в PDF: {e}")
        return None


def transliterate(text):
    """Простая транслитерация кириллицы в латиницу."""
    if not text:
        return ""
    
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch',
        'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
        'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    result = ""
    for char in text:
        result += mapping.get(char, char)
    
    return result


def export_simple_pdf(model, filename=None):
    """
    Простой экспорт - только список персон.
    Для случаев когда reportlab недоступен.
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"family_tree_simple_{timestamp}.txt"
    
    try:
        persons = list(model.get_all_persons().values())
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("🌳 Семейное древо\n")
            f.write(f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
            
            f.write("📊 Статистика:\n")
            f.write(f"  Всего персон: {len(persons)}\n")
            f.write(f"  Мужчин: {sum(1 for p in persons if p.gender == 'Мужской')}\n")
            f.write(f"  Женщин: {sum(1 for p in persons if p.gender == 'Женский')}\n")
            f.write(f"  С фото: {sum(1 for p in persons if p.has_photo())}\n\n")
            
            f.write("👥 Все персоны:\n")
            f.write("-" * 80 + "\n")
            
            for i, person in enumerate(sorted(persons, key=lambda p: p.birth_date or '9999'), 1):
                full_name = f"{person.surname} {person.name}"
                if person.patronymic:
                    full_name += f" {person.patronymic}"
                
                gender = "М" if person.gender == "Мужской" else "Ж"
                birth = person.birth_date or "?"
                death = person.death_date if person.is_deceased else "—"
                
                f.write(f"{i:3}. {full_name} ({gender}) | р. {birth} | ум. {death}\n")
                
                if person.birth_place:
                    f.write(f"     Место рождения: {person.birth_place}\n")
                if person.occupation:
                    f.write(f"     Профессия: {person.occupation}\n")
                if person.biography:
                    bio = person.biography[:200]
                    f.write(f"     Биография: {bio}{'...' if len(person.biography) > 200 else ''}\n")
                
                f.write("\n")
        
        return filename
        
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return None
