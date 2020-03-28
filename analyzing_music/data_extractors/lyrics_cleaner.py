from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from tqdm import tqdm
import re
from nltk.corpus import stopwords


def lemmatize_doc(doc):
    wordnet_lemmatizer = WordNetLemmatizer()
    return " ".join([wordnet_lemmatizer.lemmatize(word) for word in doc.split(" ")])


def stem_doc(doc):
    porter = PorterStemmer()
    return porter.stem(doc)


def remove_bracketed_measures(tmp):
    if tmp:
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


def remove_stop_words(doc):
    stop_words = set(stopwords.words('english'))
    return ' '.join([w for w in doc.split(' ') if not w in stop_words])


def lower_case(doc):
    return doc.lower()


def clean_lyrics_data(song_data):
    song_data['lyrics_cleaned'] = song_data['lyrics'].apply(remove_bracketed_measures)
    song_data['lyrics_cleaned'] = song_data['lyrics_cleaned'].apply(lower_case)
    song_data['lyrics_cleaned'] = song_data['lyrics_cleaned'].apply(remove_nonalphanumeric)
    song_data['lyrics_cleaned'] = song_data['lyrics_cleaned'].apply(remove_stop_words)
    song_data['lyrics_clean_lemmatized'] = song_data['lyrics_cleaned'].apply(lemmatize_doc)
    song_data['lyrics_clean_stemmed'] = song_data['lyrics_cleaned'].apply(stem_doc)
    return song_data
