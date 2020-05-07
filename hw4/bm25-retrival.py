import re
import string
from os import listdir, path
from os.path import join
import math

# Number of ranked output files
RANKED_OUTPUT_NUMBER = 100


PUNCTUATIONS_REGEX_COMMA = r"[,./](?!\d)"
PUNCTUATIONS_REGEX_COMMA_1 = r"(?<!\d)[,./]"
PUNCTUATIONS_REGEX = r"[" + re.escape(re.sub(r'[-,./]', "", string.punctuation, 0)) + "]"


# Unigram index dictionary
# Stores Unigrams vs InvListItem
UNIGRAM_INDEX = dict()


# Number of documents, updated when documents are loaded.
N = 0

# Average length  of documents, updated when documents are loaded.
AVG_DOCUMENT_LENGTH = 0;

# DocumentID vs dcoument length dictionary
docId_vs_dl_dict = dict()



# Unigram index delimiter and indexes
# Parameter required to read read unigram index file.
DOCUMENT_ITEM_DELIMITER = "|"

DOCID_TF_DELIMITER = ","

DOCID_TF_INDEX = 1

INV_LIST_INDEX = 1;

DOCID_INDEX = 0

TF_INDEX_IN_UNIGRAM_DICT = 0;



# TREC file constants
Q0 = "Q0"

SYSTEM_NAME = "BM25"

OUTPUT_DELIMITER = " "


# BM25 parameters
k1 = 1.2

b = 0.75

k2 = 100


def extract_inverted_index_list(inverted_list_string):
    """
    Return list of tuples in the form (DOCId, tf) from inverted_list_string
    of the form "(DOCId1, tf1) | (DOCId2, tf2) | (DOCId3, tf3)"
    :param inverted_list_string: inverted_list_string
    :return: list of tuples
    """
    return list(map(lambda item: tuple(item[1:len(item) - 1].rsplit(DOCID_TF_DELIMITER, 1)),
                    inverted_list_string.strip().split(DOCUMENT_ITEM_DELIMITER)))



def load_index(index_file_location):
    """
    load unigram index to memory
    :param index_file_location: index_file_location
    :return: None
    """
    with open(index_file_location, 'r', encoding="utf-8") as index_file:
        for posting in index_file:
            term, inverted_list_string = posting.split("->")
            UNIGRAM_INDEX[term] = extract_inverted_index_list(inverted_list_string)



def update_N_and_avgdl(raw_file_location):
    """
    Calculate document length for each document
    also avg document length
    :param raw_file_location: raw_file_location
    :return: None
    """
    total_length_of_all_document = 0
    global AVG_DOCUMENT_LENGTH, N

    for raw_filename in listdir(raw_file_location):
        print("Parsing:  " + raw_filename)
        with open(join(raw_file_location, raw_filename), 'r', encoding="utf-8") as raw_file:
            document_length = len(raw_file.read().replace("\n", "").split(" "))
            docId_vs_dl_dict[raw_filename] = document_length
            total_length_of_all_document += document_length
            N += 1

    AVG_DOCUMENT_LENGTH = total_length_of_all_document / N



def get_ni(term):
    """
    Get document frequency for term
    :param term: term
    :return: document frequency
    """
    return len(UNIGRAM_INDEX[term])



def get_query_fi(query_text, term):
    """
    Get term frequency for term in the query_text
    :param term: term
    :return: term frequency for term in the query_text
    """
    return query_text.count(term)



def get_K(doc_id):
    """
    Get K for the
    :param term: term
    :return: term frequency
    """
    return k1 * ((1 - b) + (b * (docId_vs_dl_dict[doc_id] / AVG_DOCUMENT_LENGTH)))




def update_docid_vs_bm_score_dict(docid_bmscore_dict, docid, bm_score):
    """
    Given docid_bmscore_dict, docid and bm_score
    updates the bm_score(value) by addition of bm_score
    at key docid in docid_bmscore_dict.
    :param term: docid_bmscore_dict, docid and bm_score
    :return: None
    """
    if docid in docid_bmscore_dict:
        docid_bmscore_dict[docid] += bm_score
    else:
        docid_bmscore_dict[docid] = bm_score

def sanitize_query(content):
    """
    Sanitizes the contents by removing unctuation folds case
    :param content: contents
    :return: sanitized content
    """

    content = re.sub(PUNCTUATIONS_REGEX_COMMA_1, "", content, 0)
    content = re.sub(PUNCTUATIONS_REGEX_COMMA, "", content, 0)
    content = re.sub(PUNCTUATIONS_REGEX, "", content, 0).replace("'", "")

    return re.sub(r"([\n\t])+", " ", content, 0)


def process_query(query_string):
    """
    Get results of the query
    :param query_string: query_string
    :return: results after the query is processed
             it return a dict (doc_id, bm_score)
    """
    query_string = sanitize_query(query_string)

    docid_vs_bmscore_dict = dict()
    for query_term in query_string.split(" "):

        ni = get_ni(query_term)
        qfi = get_query_fi(query_term, query_term)

        for document_item in UNIGRAM_INDEX[query_term]:

            K = get_K(document_item[DOCID_INDEX])
            fi = int(document_item[DOCID_TF_INDEX])

            bm_score = math.log(((N - ni + 0.5) / (ni + 0.5))) \
                       * (((k1 + 1) * fi) / (K + fi)) \
                       * (((k2 + 1) * qfi) / (k2 + qfi))

            # update bm_score for the given doc_id and for the given query term.
            update_docid_vs_bm_score_dict(docid_vs_bmscore_dict, document_item[DOCID_INDEX], bm_score)

    return docid_vs_bmscore_dict



def get_top_ranked_documents(docid_bmscore_dict):
    """
    The sorted and filtered result set of top 100
    :param docid_bmscore_dict: dict of (doc_id, bm_score)
    :return: list of top (doc_id, bm_score)
    """
    return sorted(docid_bmscore_dict.items(), key=lambda x: x[1], reverse=True)[:RANKED_OUTPUT_NUMBER]


def process_all_queries(queries_file_path):
    """"
    Proceses all the queries from query_file_name
    and write to output file in queries_file_path DIR
    with format Query_<query-id>_Output.txt
    :param queries_file_path: queries_file_path
    :return: None
    """
    with open(queries_file_path, 'r', encoding="utf-8") as query_file:
        for query_item in query_file:

            # Get the query_text with query_id
            query_id, query_text = query_item.strip().split("|")

            # process query
            query_output = get_top_ranked_documents(process_query(query_text))

            # write to output file
            write_query_output(query_id, query_output, path.dirname(queries_file_path),
                               "Query_" + query_id + "_Output.txt")



def write_query_output(query_id, docs, output_dir, file_name):
    """"
    Writes the the query output to files
    :query_id docs: query_id
    :param docs: list of docs
    :param output_dir: output_dir
    :param file_name: file_name
    :return:
    """
    with open(join(output_dir, file_name), 'w', encoding="utf-8") as output_file:
        rank = 1
        for doc in docs:
            # doc[0] index for doc name
            # doc[1] bm25 score
            output_file.write(OUTPUT_DELIMITER.join((query_id, Q0, doc[0], str(rank), str(doc[1]), SYSTEM_NAME)))
            output_file.write("\n")
            rank += 1


if __name__ == '__main__':
    load_index(input("Enter the full-path of index file: "))
    update_N_and_avgdl(input("Enter the location of raw_documents: "))
    process_all_queries((input("Enter queries file location : ")))
