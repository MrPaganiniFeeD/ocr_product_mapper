from rapidfuzz import process, fuzz, utils, distance
import utils as util
import yaml



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

        if count_quote > 1 and count_quote <= 2 and False:
            if rus_cnt >= eng_cnt:
                # Преобладают русские -> заменяем английские на русские
                replace_map = eng_to_rus
            elif eng_cnt > rus_cnt:
                replace_map = rus_to_eng
        else:
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
    gt_map.append(line_split[1])


correct = 0
with open(config["result_match"], 'w', encoding='utf-8') as f:
    for i, query in enumerate(ocr_inputs_clean):
        best = process.extractOne(
            query,
            prod_names_clean,
            scorer=fuzz.token_set_ratio,   
            processor=utils.default_process
        )
        if best is None:
            best_idx = -1
            best_score = 0
        else:
            best_match, best_score, best_idx = best  

        f.write(f"------index_{i}------\n")
        """
        if str(best_idx + 1) == gt_map[i]:
            correct += 1
            f.write("---------CORRECT---------\n")
        else:
            f.write("---------INCORRECT---------\n")    
        
        if gt_map[i] != "?":
            gt_map[i] = int(gt_map[i]) - 1
        else: 
            f.write("SKIIP")
            gt_map[i] = -1
        """
        
        f.write(f"Query: {query}\n")
        f.write(f"Best match: {prod_names[best_idx]} (score={best_score:.2f})\n")
        # f.write(f"Ground truth: {prod_names[gt_map[i]]}\n")

        f.write("\n")

print("Готово, результат успешно сохранён в :", config["result_match"])
        

#accuracy = correct / (len(ocr_inputs_clean) - 5)
#print(f"\nAccuracy (fuzzy only): {accuracy:.4f}")
