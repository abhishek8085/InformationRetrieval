from os import listdir
from os.path import isfile, join

import sys

UNIGRAM_INDEX_ENABLED = True
UNIGRAM_INDEX= dict()
UNIGRAM_INVETERD_INDEX_FILENAME = "UNIGRAM_INVERTED_INDEX.txt"

BIGRAM_INDEX_ENABLED = False
BIGRAM_INDEX = dict()
BIGRAM_INVETERD_INDEX_FILENAME = "BIGRAM_INVERTED_INDEX.txt"

TRIGRAM_INDEX_ENABLED = False
TRIGRAM_INDEX = dict()
TRIGRAM_INVETERD_INDEX_FILENAME = "TRIGRAM_INVERTED_INDEX.txt"


def load_all_sanitized_files(dir_path):
    for file in listdir(dir_path):
        print("Loading:  "+file)
        load_parsed_file(join(dir_path, file))


def update_unigram_index(content_tokens, document):
    """
    Updates unigram index
    :param content_tokens: sanitized file content tokens
           tokenized by space
    :param document_name: DocId
    :return: None
    """
    for token in content_tokens:

        # skip if empty token
        if token== "":
            continue

        update_index((token), UNIGRAM_INDEX, document)


def update_bigram_index(content_tokens, document):
    """
    Updates bigram index
    :param content_tokens: sanitized file content tokens
           tokenized by space
    :param document_name: DocId
    :return: None
    """
    for token_index in range(len(content_tokens)-1):

        # skip if empty token
        if content_tokens[token_index] == "" or content_tokens[token_index+1] == "":
            continue

        update_index((content_tokens[token_index], content_tokens[token_index+1]), BIGRAM_INDEX, document)



def update_trigram_index(content_tokens, document):
    """
    Updates trigram index
    :param content_tokens: sanitized file content tokens
           tokenized by space
    :param document_name: DocId
    :return: None
    """
    for token_index in range(len(content_tokens) - 2):

        # skip if empty token
        if content_tokens[token_index] == "" or content_tokens[token_index+1] == "" or content_tokens[token_index+2] == "":
            continue

        update_index((content_tokens[token_index], content_tokens[token_index+1],  content_tokens[token_index+2]), TRIGRAM_INDEX,  document)


def update_inveterd_list(inveretd_list, document):
    """
    updates the given inverted list with docment
    :param inveretd_list:  inverted list
    :param document: docId
    :return: None
    """
    if document not in inveretd_list:
        # Initializing term frequency to 1
        inveretd_list[document] = 1
    else:
        inveretd_list[document] += 1


def update_index(ngram, index, document):
    """
    update the given index with the ngram and document.
    :param ngram: ngram
    :param index: index
    :param document: doc
    :return: None
    """
    if ngram not in index:
        index[ngram] = dict()
    update_inveterd_list(index[ngram], document)


def update_indexes(content_tokens, document_name):
    """
    Updates all inverted indexes dict
    :param content_tokens: sanitized file content tokens
           tokenized by space
    :param document_name: DocId
    :return: None
    """
    if UNIGRAM_INDEX_ENABLED:
        update_unigram_index(content_tokens, document_name)
    if BIGRAM_INDEX_ENABLED:
        update_bigram_index(content_tokens, document_name)
    if TRIGRAM_INDEX_ENABLED:
        update_trigram_index(content_tokens, document_name)




def write_all_inverted_index_to_file():
    """
    writes all inverted indexes to file
    :return: None
    """
    if UNIGRAM_INDEX_ENABLED:
        write_inverted_index_to_file(UNIGRAM_INVETERD_INDEX_FILENAME, UNIGRAM_INDEX)
    if BIGRAM_INDEX_ENABLED:
        write_inverted_index_to_file(BIGRAM_INVETERD_INDEX_FILENAME, BIGRAM_INDEX)
    if TRIGRAM_INDEX_ENABLED:
        write_inverted_index_to_file(TRIGRAM_INVETERD_INDEX_FILENAME, TRIGRAM_INDEX)


def write_inverted_index_to_file(file_name, index):
    """
    write the given idex to file
    :param file_name: index_file_name
    :param index: index
    :return: None
    """
    with open(file_name, 'w', encoding="utf-8") as index_file:
        for index_item in sorted(index.items(), key = lambda x:x[0]):
            ngram_text = index_item[0] if type(index_item[0]) is str else " ".join(index_item[0])
            index_file.write(ngram_text+"->"+'|'.join('({}, {})'.format(k, v) for k, v in index_item[1].items()))
            index_file.write("\n")


def load_parsed_file(file_path):
    '''
    Reads the the graph from the file GRAPH_FILE_NAME
    and loads and pre-computes necessary information
    requires to calculate PageRank.
    :return: None
    '''
    with open(file_path, 'r', encoding="utf-8") as parsed_file:
        update_indexes(list(map(lambda s:"" if set(s.strip())==set("-") else s.strip(), parsed_file.read().split(" "))), file_path[file_path.rfind("/")+1:])



if __name__ == '__main__':
    args = set(sys.argv)
    UNIGRAM_INDEX_ENABLED = "-unigram" in args
    BIGRAM_INDEX_ENABLED = "-bigram" in args
    TRIGRAM_INDEX_ENABLED = "-trigram" in args

    if not (UNIGRAM_INDEX_ENABLED or BIGRAM_INDEX_ENABLED or TRIGRAM_INDEX_ENABLED):
        print("Index type required.")
        sys.exit(0)


    load_all_sanitized_files(sys.argv[1])
    write_all_inverted_index_to_file()