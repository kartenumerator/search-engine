import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

sentence = "NarutoloveHinata"
tokens = word_tokenize(sentence)
print(tokens)