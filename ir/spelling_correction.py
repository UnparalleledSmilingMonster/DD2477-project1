import json
from nltk.tokenize.treebank import TreebankWordTokenizer
import json
import nltk
nltk.download('punkt')
import enchant
import itertools

class Bigrams:
    def __init__(self, new = False):
        self.new = new
        if self.new:
            self.unigrams_words_counts = {}
            self.bigrams_words_counts = {}
            self.bigrams_words_probs = {}
            self.bigrams_parts = {}
        else:
            with open('bigrams_data/unigrams_words_counts.json') as json_file:
                self.unigrams_words_counts = json.load(json_file)
            with open('bigrams_data/bigrams_words_probs.json') as json_file:
                self.bigrams_words_probs = json.load(json_file)
            with open('bigrams_data/bigrams_parts.json') as json_file:
                self.bigrams_parts = json.load(json_file)
            with open('bigrams_data/bigrams_words_counts.json') as json_file:
                self.bigrams_words_counts = json.load(json_file)

        self.tokenizer = TreebankWordTokenizer()
        #self.dictionary = enchant.Dict("en_US") #Not useful anymore since the bigrams are already computed

    def tokenize_texts(self, text):
        tokens = self.tokenizer.tokenize(text)
        # keep tokens that are only letters
        tokens = [token for token in tokens if token.isalpha()]
        tokens = [token for token in tokens if self.dictionary.check(token)]

        if len(tokens) > 0:
            for i in range(len(tokens)):
                token = tokens[i].lower()
                modified_token = token.lower()
                modified_token = "^" + modified_token + "$"
                
                #split into bi-grams
                for j in range(len(modified_token)-1):
                    bigram_ = modified_token[j:j+2]
                    if bigram_ not in self.bigrams_parts:
                        self.bigrams_parts[bigram_] = [token]
                    else:
                        words = self.bigrams_parts[bigram_]
                        if token not in words:
                            words.append(token)
                        self.bigrams_parts[bigram_] = words
                
                if token in self.unigrams_words_counts:
                    self.unigrams_words_counts[token] += 1
                else:
                    self.unigrams_words_counts[token] = 1
                
                if i > 0:
                    prev_token = tokens[i-1].lower()
                    bigram = prev_token + " " + token
                    if bigram in self.bigrams_words_counts:
                        self.bigrams_words_counts[bigram] += 1
                    else:
                        self.bigrams_words_counts[bigram] = 1
    
    def calculate_bigram_probs(self):
        for k, v in self.bigrams_words_counts.items():
            words = k.split(" ")
            first_word = words[0]
            second_word = words[1]
            if first_word in self.unigrams_words_counts:
                prob = v / self.unigrams_words_counts[first_word]
                self.bigrams_words_probs[k] = prob
            else:
                self.bigrams_words_probs[k] = 0


    def run_bigrams(self):
        current_row = 1

        with open('formated_dataset.json') as json_file:
            for obj in json_file:
                dic = json.loads(obj)
                text = dic["text"]
                if not self.new:
                    # only add articles we have not seen before to the index
                    if current_row > self.bigrams_parts['latest_row_checked']:
                        self.tokenize_texts(text)
                        self.bigrams_parts['latest_row_checked'] = current_row
                else:
                    self.tokenize_texts(text)
                    self.bigrams_parts['latest_row_checked'] = current_row
                current_row += 1
                if current_row % 500 == 0:
                    print(current_row)
                    with open('bigrams_data/bigrams_words_probs.json', 'w') as outfile:
                        json.dump(self.bigrams_words_probs, outfile)
                    with open('bigrams_data/bigrams_parts.json', 'w') as outfile:
                        json.dump(self.bigrams_parts, outfile)
                    with open('bigrams_data/bigrams_words_counts.json', 'w') as outfile:
                        json.dump(self.bigrams_words_counts, outfile)
                    with open('bigrams_data/unigrams_words_counts.json', 'w') as outfile:
                        json.dump(self.unigrams_words_counts, outfile)   

        self.calculate_bigram_probs()

        # write to files
        with open('bigrams_data/bigrams_words_probs.json', 'w') as outfile:
            json.dump(self.bigrams_words_probs, outfile)
        with open('bigrams_data/bigrams_parts.json', 'w') as outfile:
            json.dump(self.bigrams_parts, outfile)
        with open('bigrams_data/bigrams_words_counts.json', 'w') as outfile:
            json.dump(self.bigrams_words_counts, outfile)
        with open('bigrams_data/unigrams_words_counts.json', 'w') as outfile:
            json.dump(self.unigrams_words_counts, outfile)    

    def jaccard(self, possible_words, bigrams):
        jaccard_scores = []
        for word in possible_words:
            modified_word = "^" + word + "$"
            word_bigrams = []

            for i in range(len(modified_word)-1):
                bigram_ = modified_word[i:i+2]
                word_bigrams.append(bigram_)

            intersection = len(set(bigrams).intersection(set(word_bigrams)))
            union = len(set(bigrams).union(set(word_bigrams)))
            jaccard_score = intersection / union
            if jaccard_score > 0.4:
                jaccard_scores.append(word)

        return jaccard_scores
    
    def edit_distance(self, word, possible_words):
        edit_distances = []
        for possible_word in possible_words:
            distance = nltk.edit_distance(word, possible_word)
            if distance <= 2:
                edit_distances.append(possible_word)
        return edit_distances
    
    def get_bigram_suggestions(self, token):
            # get all possible bigrams for the word
            word = token.lower()
            modified_word = "^" + word + "$"
            bigrams = []
            for i in range(len(modified_word)-1):
                bigram_ = modified_word[i:i+2]
                if bigram_ in self.bigrams_parts:
                    bigrams.append(bigram_)
            # get all possible words for the bigrams
            possible_words = []
            for bigram in bigrams:
                possible_words += self.bigrams_parts[bigram]
            
            possible_words = list(set(possible_words))

            passed_jaccard = self.jaccard(possible_words, bigrams)
            
            words = self.edit_distance(word, passed_jaccard)
            # rank them according to their count in the unigram_words_counts
            words = sorted(words, key=lambda x: self.unigrams_words_counts[x], reverse=True)
            return words

    def get_spelling_suggestions(self, tokens):
        # make all tokens lowercase
        tokens = [token.lower() for token in tokens]

        # only one word in the search query
        if len(tokens) == 1:
            if tokens[0].lower() in self.unigrams_words_counts:
                return [tokens[0]]
            words = self.get_bigram_suggestions(tokens[0])
            words = words[:1]
            return words
        
        else: # multiple words in the query
            # check which words are misspelled
            misspelled_words = []
            for token in tokens:
                if token.lower() not in self.unigrams_words_counts:
                    misspelled_words.append(token)

            if len(misspelled_words) == 0:
                return tokens
            
            suggestions = []
            for word in tokens:
                if word in misspelled_words:
                    suggestions.append(self.get_bigram_suggestions(word))
                else:
                    suggestions.append([word])
            
            bigram_probabilites = {}
            for i in range(len(tokens)):
                if i > 0:
                    for j in range(len(suggestions[i-1])):
                        for k in range(len(suggestions[i])):
                            bigram = suggestions[i-1][j] + " " + suggestions[i][k]
                            if bigram in self.bigrams_words_probs:
                                prob = self.bigrams_words_probs[bigram]
                                bigram_probabilites[bigram] = prob
                            else:
                                bigram_probabilites[bigram] = 0

            combinations = []
            if len(tokens) == 2:
                # get max probability
                try:
                    max_prob = max(bigram_probabilites, key=bigram_probabilites.get)
                    suggestions = max_prob.split(" ")
                except:
                    suggestions = []
            else:
                combinations = list(itertools.product(*suggestions))
                suggestions = []
                for combination in combinations:
                    sum = 0
                    product = 0
                    count = 0
                    for i in range(len(combination)-1):
                        bigram = combination[i] + " " + combination[i+1]
                        if bigram in bigram_probabilites:
                            prob = bigram_probabilites[bigram]
                            sum += prob
                            product *= prob
                            count += self.unigrams_words_counts[combination[i]]
                    count += self.unigrams_words_counts[combination[-1]]
                    suggestions.append((combination, product, sum, count))
                    # sort by product, sum and last count
                suggestions = sorted(suggestions, key=lambda x: (x[1], x[2], x[3]), reverse=True)
                suggestions = list(suggestions[0][0])
            
            return suggestions

if __name__ == "__main__":
    bigrams = Bigrams(new=False)

    print(bigrams.get_spelling_suggestions(['hello']))
    # bigrams.run_bigrams()
