import nltk
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from tqdm import tqdm
import re
import pandas as pd

def lemmatize_doc(doc):
    wordnet_lemmatizer = WordNetLemmatizer()
    return " ".join([wordnet_lemmatizer.lemmatize(word) for word in doc.split(" ")])

def stem_doc(doc):
    porter = PorterStemmer()
    return porter.stem(doc)

def remove_bracketed_measures(tmp):
    start_find = ["["]
    for s in tqdm(start_find):
        while (tmp.find(s) != -1):
            firstDelPos= tmp.find(s) # get the position of [
            secondDelPos=tmp[firstDelPos:].find("]") + firstDelPos # get the position of ]
            if firstDelPos > secondDelPos:
                return tmp
            tmp = tmp.replace(tmp[firstDelPos:secondDelPos+1], "") # replace the string between two delimiters
    return tmp

def remove_nonalphanumeric(word):
    return " ".join([re.sub('[\W_]+', '', w) for w in word.split(' ')])

def remove_verse_workds(word):
    for remove_word in ['intro', 'verse', 'chorus', 'instrumental break']:
        word = " ".join([re.sub(remove_word, '', w) for w in word.split(' ')])
    return word