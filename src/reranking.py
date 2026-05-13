from rapidfuzz import process, fuzz, utils, distance
import utils as util
import yaml


def cascade_match_full(query: str, products: list, top_k=10):
    q_prod, q_man = util.parse_product_full(query)
    if not q_prod:
        q_prod = query 

    parsed_products = [util.parse_product_full(p) for p in products]
    print(q_prod, q_man)

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
        _, cand_man = parsed_products[idx]
        
        if q_man and cand_man:
            man_score = fuzz.token_set_ratio(q_man.lower(), cand_man.lower()) / 100.0
        else:
            man_score = 0.5
        
        
        total = (1.0 * name_score/100) + (0.2 * man_score)
        
        if total > best_total_score:
            best_total_score = total
            best_idx = idx
    
    return best_idx if best_idx is not None else candidates[0][2]

with open('./config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)



ocr_inputs = util.load_file(config["ocr_inputs"])
prod_names = util.load_file(config["prod_names"])


eng_all = "qwertyuiopasdfghjklzxcvbnm"
rus_all = "йцукенгшщзхъфывапролджэячсмить"

eng_set = set(eng_all)   # {'a', 'b', 'c', ...}
rus_set = set(rus_all)   # {'й', 'ц', ...}


def create_db_char(lines: list[str]):
    result = set()
    for line in lines:
        line.lower()
        words = line.split()
        for word in words:
            for char in word:
                result.add(char)

    return result


eng_to_rus = util.get_map_dict("./data/dict_mapping/eng_to_rus.txt")
rus_to_eng = {v: k for k, v in eng_to_rus.items()}


exception_words = util.get_map_dict("./data/dict_mapping/exception_words.txt")
num_to_rus = util.get_map_dict("./data/dict_mapping/num_to_rus.txt")

def replace_word(word, exception_words: {}):
    if word in exception_words.keys():
        return exception_words[word]
    return word


def fix_word(words: str, eng_to_rus: {}, rus_to_eng: {}, num_to_rus: {}, exception_words: {}) -> str:
    count_quote = 0
    results = []
    for word in words:
        if count_quote == 2:
            count_quote = 0

        word = replace_word(word, exception_words)

        rus_cnt = 0
        eng_cnt = 0
        for ch in word:
            if ch == '"':
                count_quote += 1
            if ch in rus_set:
                rus_cnt += 1
            elif ch in eng_set:
                eng_cnt += 1

        count_char = rus_cnt + eng_cnt

        if count_char > 0:
            word = [num_to_rus.get(ch, ch) for ch in word]

        replace_map = eng_to_rus
        
        word = [replace_map.get(ch, ch) for ch in word]
        results.append(''.join(word))
    return results



def preprocess_lines(lines: list[str]) -> list[str]:
    result = []
    quote = 0
    for line in lines:
        words = line.split()
        fixed_words = fix_word(words, eng_to_rus, rus_to_eng, num_to_rus, exception_words)
        result.append(' '.join(fixed_words))
    return result

ocr_inputs_clean = preprocess_lines(ocr_inputs)
prod_names_clean = preprocess_lines(prod_names)



gt_map = []

gt_map_txt = util.load_file(config["gt_match"])
for line in gt_map_txt:
    line_split = line.split()
    if line_split[1] != "?":
            line_split[1] = int(line_split[1]) - 1
    else: 
        line_split[1] = -1
    gt_map.append(line_split[1])


correct = 0
with open(config["result_match"], 'w', encoding='utf-8') as f:
    for i, query in enumerate(ocr_inputs_clean):
        best_idx = cascade_match_full(query, prod_names_clean, top_k=10)


        f.write(f"------index_{i}------\n")
        """
        if best_idx == gt_map[i]:
            correct += 1
            f.write("---------CORRECT---------\n")
        else:
            f.write("---------INCORRECT---------\n")    
        
        """
        f.write(f"Query: {query}\n")
        f.write(f"Best match: {prod_names_clean[best_idx ]} (best_idx: {best_idx})\n")
        # f.write(f"Ground truth: {prod_names_clean[gt_map[i]]}, gt_map: {gt_map[i]}\n")

        f.write("\n")

print("Готово, результат успешно сохранён в :", config["result_match"])
        

# accuracy = correct / (len(ocr_inputs_clean) - 3)
# print(f"\nAccuracy (fuzzy only): {accuracy:.4f}")
