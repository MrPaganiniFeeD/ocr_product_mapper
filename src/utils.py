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
