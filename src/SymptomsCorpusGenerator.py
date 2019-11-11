import string
from nltk.corpus import stopwords 
from nltk.tokenize import wordpunct_tokenize

l_stop_words = set(stopwords.words('english'))
l_punct = list(string.punctuation)

file_snomed_ids = "../data/snomed_ids.txt"
file_snomed_desc = "../data/sct2_Description_Full-en_INT_20180731.txt"
file_symptoms = "../data/snomed_symptoms_corpus.txt"
l_snomed_symptom_ids = set()

# reading all the symptom ids
with open(file_snomed_ids, 'r') as SFH:
    for line in SFH:
        l_snomed_symptom_ids.add(line.rstrip())

s_FH = open(file_symptoms, 'w+')
with open(file_snomed_desc, 'r') as FH:
    for line in FH:
        # skip the first line
        l_line_tokens = line.rstrip().split('\t')
        s_sym_concept_id = l_line_tokens[4]
        if s_sym_concept_id in l_snomed_symptom_ids:
            s_symptom_concept = l_line_tokens[7]
            l_concept_tokens = wordpunct_tokenize(s_symptom_concept)
            l_concept_terms = []
            for token in l_concept_tokens:
                token = token.lower()
                if token not in l_punct \
                and len(token) > 2 \
                and token not in l_stop_words:
                    l_concept_terms.append(token)
            s_FH.write(' '.join(l_concept_terms) + "\n")
s_FH.close()