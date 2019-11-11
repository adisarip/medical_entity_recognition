import re
import sys
import json
import preprocessor as tweet_processor
from os import walk
import multiprocessing as mp

d_all_symptoms_tups = {}
data_root_dir = "/Users/aditya/MTech/2019_sem4/IRE/projects/medical_entity_recognition/data/TwitterData/"
#HappyEmoticons
emoticons_happy = set([
    ':-)', ':)', ';)', ':o)', ':]', ':3', ':c)', ':>', '=]', '8)', '=)', ':}',
    ':^)', ':-D', ':D', '8-D', '8D', 'x-D', 'xD', 'X-D', 'XD', '=-D', '=D',
    '=-3', '=3', ':-))', ":'-)", ":')", ':*', ':^*', '>:P', ':-P', ':P', 'X-P',
    'x-p', 'xp', 'XP', ':-p', ':p', '=p', ':-b', ':b', '>:)', '>;)', '>:-)',
    '<3'
    ])

# Sad Emoticons
emoticons_sad = set([
    ':L', ':-/', '>:/', ':S', '>:[', ':@', ':-(', ':[', ':-||', '=L', ':<',
    ':-[', ':-<', '=\\', '=/', '>:(', ':(', '>.<', ":'-(", ":'(", ':\\', ':-c',
    ':c', ':{', '>:\\', ';('
    ])

#combine sad and happy emoticons
emoticons = emoticons_happy.union(emoticons_sad)

#Emoji patterns
emoji_pattern = re.compile("["
         u"\U0001F600-\U0001F64F"  # emoticons
         u"\U0001F300-\U0001F5FF"  # symbols & pictographs
         u"\U0001F680-\U0001F6FF"  # transport & map symbols
         u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
         u"\U00002702-\U000027B0"
         u"\U000024C2-\U0001F251"
         "]+", flags=re.UNICODE)


def clean_tweets(tweet_text):
    #after tweepy preprocessing the colon symbol left remain after
    #removing mentions
    tweet_text = re.sub(r':', '', tweet_text)
    tweet_text = re.sub(r'‚Ä¶', '', tweet_text)
    #replace consecutive non-ASCII characters with a space
    tweet_text = re.sub(r'[^\x00-\x7F]+',' ', tweet_text)
    #remove emojis from tweet
    tweet_text = emoji_pattern.sub(r'', tweet_text)
    return tweet_text


def get_match_count(xtup, xsymlist):
    count = 0
    curr_index = 0
    for term in xtup:
        if term in xsymlist:
            if xsymlist.index(term) > curr_index or xsymlist.index(term) == 0:
                curr_index = xsymlist.index(term)
                count += 1
    return count


def check_for_medical_tweet(l_tweet_terms):
    is_medical_tweet = False
    # collect all the symptoms from tweet
    l_all_tweet_sym = []
    for term in l_tweet_terms:
        if d_all_symptoms_tups.get(term) != None:
            if term not in l_all_tweet_sym:
                l_all_tweet_sym.append(term)
    # only seleting tweets with atleast 2 symptoms
    if (len(l_all_tweet_sym) < 2):
        return False, 0, None
    # collect all the sym tuples related to all the
    # sym tweet terms collected above
    set_all_sym_tups = set()
    for term in l_all_tweet_sym:
        l_tups = d_all_symptoms_tups[term]
        for tup in l_tups:
            set_all_sym_tups.add(tup)
    max_match_count = 0
    max_match_tuple = tuple()
    for tup in set_all_sym_tups:
        # matching current syms tuple with tweet syms to get best match
        match_count = get_match_count(tup, l_all_tweet_sym)
        if (max_match_count < match_count and match_count >=2):
            max_match_count = match_count
            max_match_tuple = tup
    if (max_match_count >= 2):
        is_medical_tweet = True
    return is_medical_tweet, max_match_count, max_match_tuple


def get_annotated_tweet(xtup, l_tweet_terms):
    is_tagging_in_progress = False
    d_annotated_terms = {}
    for idx in range(0, len(l_tweet_terms)):
        term = l_tweet_terms[idx]
        if term in xtup:
            if (is_tagging_in_progress == False):
                d_annotated_terms[term] = "B-Symptom"
                is_tagging_in_progress = True
            else:
                d_annotated_terms[term] = "I-Symptom"
        else:
            d_annotated_terms[term] = "O"
            is_tagging_in_progress = False
    return d_annotated_terms


def build_symptoms_dict(file_sym_corpus):
    with open(file_sym_corpus, 'r') as FH:
        for line in FH:
            l_line_tokens = line.rstrip().split()
            sym_tup = tuple(l_line_tokens)
            for token in l_line_tokens:
                if d_all_symptoms_tups.get(token) == None:
                    d_all_symptoms_tups[token] = [sym_tup]
                else:
                    if sym_tup not in d_all_symptoms_tups[token]:
                        d_all_symptoms_tups[token].append(sym_tup)


def medical_tweet_extractor(q_json_files):
    xfh = open(data_root_dir+"medical_tweets_"+mp.current_process().name+".txt", "w+")
    xfh.write("Document ID,Sentence #,Word,Tag\n")
    n_idx = 0
    while not q_json_files.empty():
        try:
            file_name = q_json_files.get(False)
            print("[INFO] "+mp.current_process().name+":Processing File:", file_name)
            with open(file_name, 'r', errors='ignore') as JFH:
                for line in JFH:
                    is_medical_tweet = False
                    tweet = json.loads(line)
                    if (tweet.get("text") != None):
                        tweet_lang = "en" if tweet.get("lang") == "en" else "NA"
                        if tweet_lang != "NA":
                            if tweet.get("extended_tweet") != None:
                                tweet_text = tweet["extended_tweet"]["full_text"]
                            else:
                                tweet_text = tweet["text"]
                            clean_text = tweet_processor.clean(tweet_text)
                            filtered_tweet = clean_tweets(clean_text)
                            l_tweet_text_processed = filtered_tweet.split()
                            is_medical_tweet, count, tup = check_for_medical_tweet(l_tweet_text_processed)
                            if (is_medical_tweet == True):
                                d_annotated_tweet = get_annotated_tweet(tup, l_tweet_text_processed)
                                for term in d_annotated_tweet:
                                    xfh.write(','.join([str(n_idx),str(n_idx),term,d_annotated_tweet[term]])+"\n")
                                n_idx += 1
        except Exception as exp:
            print("Execption in Process:", mp.current_process().name, file_name)
            print(mp.current_process().name, exp)
            pass
    xfh.close()
    
def main():
    # build symptoms dictionary
    file_sym_corpus = data_root_dir + "snomed_symptoms_corpus.txt"
    build_symptoms_dict(file_sym_corpus)

    # get json files list
    q_json_files = mp.Queue()
    with open(data_root_dir+"json_files_list.txt", "r") as FH:
        for line in FH:
            q_json_files.put(data_root_dir+line.rstrip())

    n_processes = 10
    l_processes = [mp.Process(target=medical_tweet_extractor,
                              args=(q_json_files,))
                              for x in range(n_processes)]
    
    for p in l_processes:
        p.start()

    for p in l_processes:
        p.join()

        
if __name__ == '__main__':
    main()