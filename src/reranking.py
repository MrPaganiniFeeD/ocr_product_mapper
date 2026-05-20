from rapidfuzz import process, fuzz, utils, distance
import utils as util
import yaml

CONFIG_PATH = "./config.yaml"

def cascade_match_full(config, query: str, parsed_products: list, top_k=10):
    q_prod, q_man, q_storage = util.parse_product_full(query)
    if not q_prod:
        q_prod = query

    candidates = process.extract(
        q_prod,
        [p[0] for p in parsed_products],
        scorer=fuzz.token_set_ratio,
        processor=utils.default_process,
        limit=top_k
    )

    best_idx = None
    best_total_score = -1

    for cand_name, name_score, idx in candidates:
        _, cand_man, cand_temp = parsed_products[idx]
        if q_man and cand_man:
            man_score = fuzz.token_set_ratio(q_man.lower(), cand_man.lower()) / 100.0
        else:
            man_score = 0.5

        if q_storage and cand_temp:
            temp_score = fuzz.token_set_ratio(q_storage, cand_temp) / 100.0
        else:
            temp_score = 0.2

        total = (config["coef_product"] * name_score/100) + (config["coef_manufacturer"] * man_score) + (config["coef_temp"] * temp_score)

        total_norm = total / (config["coef_product"] + config["coef_manufacturer"] + config["coef_temp"])
        if total_norm > best_total_score:
            best_total_score = total_norm
            best_idx = idx
    
    return best_idx, total_norm, name_score, man_score, temp_score




def load_config(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        return config


def replace_word(word, exception_words: {}):
    if word in exception_words.keys():
        return exception_words[word]
    return word


def fix_word(config, words: str, eng_to_rus: {}, rus_to_eng: {}, num_to_rus: {}, exception_words: {}) -> str:
    eng_all = "qwertyuiopasdfghjklzxcvbnm"
    rus_all = "йцукенгшщзхъфывапролджэячсмить"

    eng_set = set(eng_all)   # {'a', 'b', 'c', ...}
    rus_set = set(rus_all)   # {'й', 'ц', ...}

    results = []

    for word in words:
        word = replace_word(word, exception_words)

        rus_cnt = 0
        eng_cnt = 0
        for ch in word:
            if ch in rus_set:
                rus_cnt += 1
            elif ch in eng_set:
                eng_cnt += 1

        count_char = rus_cnt + eng_cnt
        if count_char > 1:
            word = [num_to_rus.get(ch, ch) for ch in word]

        replace_map = eng_to_rus

        word = [replace_map.get(ch, ch) for ch in word]
        results.append(''.join(word))
    return results

def preprocess_lines(lines: list[str]) -> list[str]:
    result = []
    for line in lines:
        words = line.split()
        fixed_words = fix_word(config, words, eng_to_rus, rus_to_eng, num_to_rus, exception_words)
        result.append(' '.join(fixed_words))
    return result

### ЗАГРУЗКА КОНФИГА
config = load_config(CONFIG_PATH)

### ЗАГРУКА DB И OCR_INPUTS
ocr_inputs = util.load_file(config["ocr_inputs"])
prod_names = util.load_file(config["prod_names"])

### ЗАГРУЗКА СЛОВАРЕЙ
eng_to_rus = util.get_map_dict("./data/dict_mapping/eng_to_rus.txt")
rus_to_eng = {v: k for k, v in eng_to_rus.items()}

exception_words = util.get_map_dict("./data/dict_mapping/exception_words.txt")
num_to_rus = util.get_map_dict("./data/dict_mapping/num_to_rus.txt")


### ПРЕПРОЦЕССИНГ DB И INPUTS
ocr_inputs_clean = preprocess_lines(ocr_inputs)
prod_names_clean = preprocess_lines(prod_names)

parsed_products = [util.parse_product_full(p) for p in prod_names_clean]


### ЭТО НУЖНО ДЛЯ МЕТРИК
gt_map = []

gt_map_txt = util.load_file(config["gt_match"])
for line in gt_map_txt:
    line_split = line.split()
    if line_split[1] != "?":
            line_split[1] = int(line_split[1]) - 1
    else: 
        line_split[1] = -1
    gt_map.append(line_split[1])

### ОСНОВНОЙ PIPELINE и подсчёт точности на OCR_INPUTS.txt
correct = 0
with open(config["result_match"], 'w', encoding='utf-8') as f:
    for i, query in enumerate(ocr_inputs_clean):
        best_idx = cascade_match_full(config, query, parsed_products, top_k=10)[0]


        f.write(f"------index_{i}------\n")

        """
        if best_idx == gt_map[i]:
            correct += 1
            f.write("---------CORRECT---------\n")
        else:
            f.write("---------INCORRECT---------\n")  
        
        """

        f.write(f"Query: {query}\n")
        f.write(f"Best match: {prod_names_clean[best_idx]} (best_idx: {best_idx})\n")
        # f.write(f"Ground truth: {prod_names_clean[gt_map[i]]}, gt_map: {gt_map[i]}\n")

        f.write("\n")

print("Готово, результат успешно сохранён в :", config["result_match"])
        
# accuracy = correct / (len(ocr_inputs_clean) - 3)
# print(f"\nAccuracy (fuzzy only): {accuracy:.4f}")
