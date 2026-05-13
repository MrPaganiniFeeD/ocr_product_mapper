import re

def load_file(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def get_map_dict(file_path: str):
    map_dict = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            key, value = line.rstrip('\n').split(":")
            map_dict[key] = value
    return map_dict


def parse_product_full(text: str):
    """
    Возвращает (product_name, manufacturer, storage_condition)
    Поддерживает непарные кавычки:
    - "Производитель" -> ('название', 'Производитель')
    - "Производитель  -> ('название', 'Производитель')
    - Производитель"  -> ('название', 'Производитель')
    """
    text = text.strip()
    
    # --- 1. Ищем производителя (в кавычках, включая непарные) ---
    manufacturer = ''
    
    # Сначала ищем парные кавычки (самый надёжный вариант)
    pair_match = re.search(r'"([^"]+)"', text)
    if pair_match:
        manufacturer = pair_match.group(1)
        # Удаляем эту часть из текста (вместе с кавычками)
        text = text.replace(f'"{manufacturer}"', '')
    else:
        # Ищем только открывающую кавычку: "Слово (без закрытия) до пробела или конца строки
        open_match = re.search(r'"([^"\s]+)', text)
        if open_match:
            manufacturer = open_match.group(1)
            text = text.replace(f'"{manufacturer}', '')
        else:
            # Ищем только закрывающую кавычку: слово без открывающей кавычки, заканчивающееся на "
            close_match = re.search(r'([^"\s]+)"', text)
            if close_match:
                manufacturer = close_match.group(1)
                text = text.replace(f'{manufacturer}"', '')
    

    # --- 3. Оставшийся текст — это название товара ---
    product = re.sub(r'\s+', ' ', text).strip()
    
    return product, manufacturer