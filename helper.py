import os
from urllib.parse import urlparse
import re


def check_url_extension(url):
    # 1. Parse the URL to isolate the path
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # 2. Extract the extension (e.g., '.php', '.pdf', '.jpg')
    _, ext = os.path.splitext(path)
    
    # Standard web pages often have no extension, or end in .html, .htm, or .php
    html_extensions = {'.html', '.htm', '.php', '.asp', '.aspx'}
    if ext == '':
        return False,ext
    for extnsn in html_extensions:
        if extnsn.lower() in ext.lower() :
            return False,ext
        
    # if ext.lower() not in html_extensions:
    #     return True, ext
    # else:
    return True, ext


def check_only_english_alphanum_symbols(word):
    # Regex: Allow letters, numbers, and common ASCII symbols
    # This pattern covers standard ASCII 32-126
    pattern = r'^[ -~]+$' 
    
    # Alternatively, define specifically: letters, digits, and specific symbols
    # pattern = r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$'

    if re.match(pattern, word):
        return True
    return False

def jaccard_distance(str1, str2):
    # Convert strings to sets of words
    a = set(generate_kgrams(str1.lower()))
    b = set(generate_kgrams(str2.lower()))
    
    # print(a)
    # print(b)
    # Calculate Jaccard Similarity
    intersection = len(a.intersection(b))
    union = len(a.union(b))
    # print(intersection, union)
    # Calculate Jaccard Distance
    return 1 - (intersection/union) if union != 0 else 1 

def generate_kgrams(word, k=3):
    word = f"${word}$"
    return [word[i:i+k] for i in range(len(word) - k + 1)]
