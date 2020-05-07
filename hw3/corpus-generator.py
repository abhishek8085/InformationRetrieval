import re
import string
import sys

import time

import os
from bs4 import BeautifulSoup

CASE_FOLDING = True
PUNCTUATION_REMOVAL = True
LINKS_WITH_CONTENT_PATH = ""

LINK_IDENTIFIER = "LINK:"
BODY_BEGIN_IDENTIFIER = "BODY BEGIN"
BODY_END_IDENTIFIER = "BODY END"
PUNCTUATIONS_REGEX_COMMA = r"[,./](?!\d)"
PUNCTUATIONS_REGEX_COMMA_1 = r"(?<!\d)[,./]"
PUNCTUATIONS_REGEX = r"[" + re.escape(re.sub(r'[-,./]', "", string.punctuation, 0)) + "]"


def write_parsed_file(file_name, file_content):
    '''
    Write the sanitised corpus to file.
    :param file_name: file names
    :param file_content: file compent
    :return:
    '''
    with open(file_name, 'w', encoding="utf-8") as output_file:
        output_file.write(file_content)


def get_filename(link):
    """
    Generate file name from the URL
    :param link: URL
    :return: extract the filename
    """
    return link[link.rfind("/") + 1:]


def sanitize_content(content):
    """
    Sanitizes the contents by removing HTML tags, punctuation
    and folds case if needed
    :param content: raw contents
    :return: sanitized content
    """

    # stripping all HTML TAGS
    content = BeautifulSoup(content).find("div", {"id": "content", "role": "main"}).get_text()

    if CASE_FOLDING:
        # case folding
        content = content.lower()
    if PUNCTUATION_REMOVAL:

        # Removing punctuation.
        content = re.sub(PUNCTUATIONS_REGEX_COMMA_1, "", content, 0)
        content = re.sub(PUNCTUATIONS_REGEX_COMMA, "", content, 0)
        content = re.sub(PUNCTUATIONS_REGEX, "", content, 0).replace("'", "");

    return re.sub(r"([\n\t])+", " ", content, 0)


def start_corpus_generation():
    '''
    Reads the contents of raw URL with contents file
    sanitizes and writes sanitized file.
    :return: None
    '''
    with open(LINKS_WITH_CONTENT_PATH, 'r', encoding="utf-8") as content_file:

        # initialize sanitized_output_file and content to Empty String.
        sanitized_output_file_name = ""
        sanitized_output_file_content = ""

        # initialize body started flag to False
        body_stared = False

        for line in content_file:

            line = line.strip()

            # Skip if empty line
            if line == "":
                continue

            # If the line start with LINK_IDENTIFIER then its URLS
            # from which output_filename can be extracted.
            if line.startswith(LINK_IDENTIFIER):
                sanitized_output_file_name = get_filename(line[line.index(LINK_IDENTIFIER):])
                title = sanitized_output_file_name.replace("_", "")
                sanitized_output_file_content += title

            # If the line is BODY_BEGIN_IDENTIFIER
            # Then its the indication of start of the content
            # for the URL found previously.
            elif line == BODY_BEGIN_IDENTIFIER:
                body_stared = True
                continue

            # If the line the is BODY_END_IDENTIFIER
            # it marks the end of the content
            elif line == BODY_END_IDENTIFIER:
                body_stared = False
                sanitized_output_file_name = "./sanitised_output/" + sanitized_output_file_name
                sanitized_output_file_name += ".txt"
                print("Writing file: " + sanitized_output_file_name)
                write_parsed_file(sanitized_output_file_name, sanitize_content(sanitized_output_file_content))

                sanitized_output_file_name = ""
                sanitized_output_file_content = ""

            # collect the content in sanitized_output_file_content
            # until body_stared is false.
            if body_stared:
                sanitized_output_file_content += (line + "\n")


if __name__ == '__main__':
    args = set(sys.argv)
    if not os.path.isdir("./sanitised_output/"):
        os.makedirs(os.path.dirname("./sanitised_output/"))
    CASE_FOLDING = "-noCaseFolding" not in args
    PUNCTUATION_REMOVAL = "-noPunRemoval" not in args
    LINKS_WITH_CONTENT_PATH = sys.argv[1]
    start = time.clock()
    start_corpus_generation()
    print("Time taken:"+str(time.clock() - start))
