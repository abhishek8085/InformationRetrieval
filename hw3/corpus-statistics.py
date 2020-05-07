import sys

import time

INDEX_DELIMITER = "->"
DOCUMENT_ITEM_DELIMITER = "|"

ngram_tf_dict = dict()
ngram_df_dict = dict()


INDEX_FILE_NAME =""


def get_tf(document_item):
    """
    Get TF for given document item i.e. (docId, tf)
    :param document_item: document_item
    :return: tf
    """
    return int(document_item[1:len(document_item)-1].split(", ")[1].strip())


def get_total_tf(inverted_list):
    """
    Gets the total term frequency of the inverted list.
    :param inverted_list: inverted list (DOC1, 5), (DOC2, 10)
    :return: total tf i.e.  for the given example 15
    """
    total_tf = 0
    for document_item in inverted_list.split(DOCUMENT_ITEM_DELIMITER):
        total_tf += get_tf(document_item)
    return total_tf


def update_tf_freq(n_gram, inverted_list):
    """
    updates the total ngram occurrence count
    :param n_gram: n_gram
    :param inverted_list: inverted_list
    :return: total n-gram tf or occurrence count
    """
    ngram_tf_dict[n_gram] = get_total_tf(inverted_list)


def get_documets_list(inverted_list):
    """
    get all the doc-id in the inverted list
    :param inverted_list: inverted _list
    :return: list of doc-ids
    """
    return list(map(lambda x:x[1:len(x)-1].split(", ")[0].strip(), inverted_list.split(DOCUMENT_ITEM_DELIMITER)))


def update_df_freq(n_gram, inverted_list):
    """
    Updates the df for the given n_gram in given inverted list
    :param n_gram: n_gram
    :param inverted_list: inverted_list
    :return: None
    """
    document_list = get_documets_list(inverted_list)
    ngram_df_dict[n_gram]=(document_list, len(document_list))



def read_index_file():
    """
    Reads and loads the index files created but inverted-indexer.
    :return: None
    """
    with open(INDEX_FILE_NAME, 'r', encoding="utf-8") as index_file:
        for index_item in index_file:

            # strip carriage return
            index_item = index_item.strip()

            #skip if emty line
            if index_item == "": continue

            # split ngram and inverted list using INDEX_DELIMITER
            n_gram, inverted_list = index_item.split(INDEX_DELIMITER)
            if n_gram =="":
                print("aln")

            update_tf_freq(n_gram, inverted_list)
            update_df_freq(n_gram, inverted_list)


def write_tf_file():
    """
    Write n-grams and total term frequency into file.
    :return: None
    """
    with open(INDEX_FILE_NAME[:INDEX_FILE_NAME.rfind(".")]+"_TF_STATS.txt", 'w', encoding="utf-8") as stats_file:
        for n_gram, tf in sorted(ngram_tf_dict.items(), key=lambda x:x[1], reverse=True):
            stats_file.write(n_gram+"|"+str(tf)+"\n")


def write_df_file():
    """
    Write n-gram, document-list, document frequency into df file.
    :return: None
    """
    with open(INDEX_FILE_NAME[:INDEX_FILE_NAME.rfind(".")] + "_DF_STATS.txt", 'w', encoding="utf-8") as stats_file:
        for n_gram, df_item in sorted(ngram_df_dict.items(), key=lambda x: x[0]):
            stats_file.write(n_gram + "|" + " ".join(df_item[0]) +"|"+ str(df_item[1])+ "\n")




if __name__ == '__main__':
    INDEX_FILE_NAME = sys.argv[1]
    start = time.clock()
    print("Started stats calculation.")
    read_index_file()
    write_tf_file()
    write_df_file()
    print("Time taken:" + str(time.clock() - start))