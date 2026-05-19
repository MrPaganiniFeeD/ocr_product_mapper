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
    Возвращает (product_name, manufacturer, temperature)
    """
    text = text.strip()

    manufacturer = ''
    pair_match = re.search(r'"([^"]+)"', text)
    if pair_match:
        manufacturer = pair_match.group(1)
        text = text.replace(f'"{manufacturer}"', '')
    else:
        open_match = re.search(r'"([^"\s]+)', text)
        if open_match:
            manufacturer = open_match.group(1)
            text = text.replace(f'"{manufacturer}', '')
        else:
            close_match = re.search(r'([^"\s]+)"', text)
            if close_match:
                manufacturer = close_match.group(1)
                text = text.replace(f'{manufacturer}"', '')

    text = re.sub(r'([+-])\s*([()]*)\s*(\d)', r'\1\3', text)
    text = re.sub(r'([+-]?\d+)\s*[()]+\s*([+-]?\d+)', r'\1 \2', text)

    temperature = ''
    numbers = re.findall(r'[+-]?\d+(?:\.\d+)?', text)

    if len(numbers) >= 2:
        temperature = ' '.join(numbers[:2])
        for num in numbers[:2]:
            text = text.replace(num, '', 1)
    elif len(numbers) == 1:
        temperature = numbers[0]
        text = text.replace(numbers[0], '', 1)

    text = re.sub(r'(?<!\d)[+-](?!\d)', '', text)
    text = re.sub(r'\(\s*\)', '', text)
    product = re.sub(r'\s+', ' ', text).strip()

    return product, manufacturer, temperature