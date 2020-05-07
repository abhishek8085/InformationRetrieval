import re
import sys
from urllib import request

import nltk
import time
from bs4 import BeautifulSoup
from nltk.corpus import words

SEED_URL = "https://en.wikipedia.org/wiki/Solar_eclipse"

POLITENESS_POLICY_DELAY_IN_SEC = 1
MAXIMUM_CRAWL_DEPTH = 6
PREFIX_TO_FOLLOW = "https://en.wikipedia.org/wiki"
UNIQUE_URL_THRESHOLD = 1000
LINK_WITH_CONTENT_FILE_NAME = "task1_links_with_content.txt"
LINKS_FILE_NAME = "G1_LINKS.txt"
GRAPH_FILE_NAME = "G1.txt"

# Frontier (list of frontier-item)
# A frontier-item is tuple (<Anchor-Text>, <URL>, <DEPTH>, <DOC_ID>, <INLINKS_SET>)
# Anchor-Text : is the Anchor-Text
# URL : the URL hyperlink points to.
# DEPTH : depth at which this was found
frontier = []

# frontier-item selector indexes
FRONTIER_ITEM_ANCHOR_TEXT_INDEX = 0
FRONTIER_ITEM_URL_INDEX = 1
FRONTIER_ITEM_DEPTH_INDEX = 2
FRONTIER_ITEM_DOC_ID_INDEX = 3
FRONTIER_ITEM_INLINK_SET_INDEX = 4

# visited links
visited = dict()




# files to document link and content
links_with_content_file = open(LINK_WITH_CONTENT_FILE_NAME, 'w', encoding="utf-8")
links_file = open(LINKS_FILE_NAME, 'w', encoding="utf-8")


# stemmer to stem words
stemmer = nltk.stem.porter.PorterStemmer()

# English dictionary to de-compund words.
english_words_set = set(filter(lambda w: len(w) > 1, words.words())).union({""})

# flag that enable raw-content writing to files.
SHOULD_WRITE_RAW_CONTENT = False

# doc id
doc_id_count = 0

def get_next_docid():
    global doc_id_count
    doc_id_count += 1
    return str("D"+str(doc_id_count))

# This where the crawling starts
def start_crawling(seed_url, keyword=None):
    # Add Sed URL to frontier
    frontier.append(("Seed", seed_url, 1, get_next_docid(), set()))

    # start crawling
    internal_start_crawling(keyword)

    write_graph_file()

    # release all the resources
    release_resources()

# closes the links and link with content files.
def release_resources():
    links_with_content_file.close()
    links_file.close()


def get_content_body(raw_html_soup):
    '''
    Filters out the content body. using div id and role.
    :param raw_html_soup: raw html
    :return: the content div element.
    '''
    return raw_html_soup.find("div", {"id": "content", "role": "main"})


def write_raw_content(hyperlink, html_content_body):
    links_with_content_file.write("LINK:" + hyperlink + "\n")
    links_with_content_file.write("BODY BEGIN\n" + str(html_content_body) + "\nBODY END\n\n")


def write_graph_file():
    with open(GRAPH_FILE_NAME, 'w', encoding="utf-8") as graph_file:
        for frontier_item in sorted(visited.values(), key = lambda x : int(x[FRONTIER_ITEM_DOC_ID_INDEX][1:])):
            graph_file.write(frontier_item[FRONTIER_ITEM_DOC_ID_INDEX]+" "+
                             " ".join(sorted(frontier_item[FRONTIER_ITEM_INLINK_SET_INDEX], key=lambda x : int(x[1:]))) )
            graph_file.write("\n")


def document_link_and_content(hyperlink_count, anchor_text, hyperlink, depth, new_depth, html_content_body, docid):
    if new_depth:
        links_file.write("\n\n\nDEPTH:" + str(depth) + "\n")
    links_file.write(str(hyperlink_count) + "|" + docid + "|" + anchor_text + "|" + hyperlink + "\n")
    links_file.flush()

    if SHOULD_WRITE_RAW_CONTENT:
        write_raw_content(hyperlink, html_content_body)




def is_link_external(hyperlink):
    '''
    :param hyperlink: hyperlink
    :return: Return true if the link is outside of PREFIX_TO_FOLLOW
             False, otherwise.
    '''
    return not hyperlink.startswith(PREFIX_TO_FOLLOW)


def is_link_visited(hyperlink):
    '''
    :param hyperlink: hyperlink
    :return: True, if the link is already visited or
             presented in the frontier.
             False, otherwise.
    '''
    return hyperlink in visited


def is_link_administrative(hyperlink):
    '''
    :param hyperlink: hyperlink
    :return: True, if the link is administrative
             i.e. contains ':'
             False, otherwise.
    '''
    return hyperlink.count(":") > 1


def is_link_for_page_section(hyperlink):
    '''
    :param hyperlink: hyperlink
    :return: True, if the link of page section
             i.e. starts with #.
             False, otherwise.
    '''
    return hyperlink.startswith("#")


def is_link_pointing_to_english_article(hyperlink):
    '''
    :param hyperlink: hyperlink
    :return: True, if the link of english article
             i.e. of the form "en.wikipedia".
             False, otherwise.
    '''
    return hyperlink.count("en.wikipedia") > 0

def is_link_pointing_to_main_page(hyperlink):
    '''
    :param hyperlink: hyperlink
    :return: True, if the link pointing to main page
             i.e. "https://en.wikipedia.org/wiki/Main_Page" or
              "https://www.wikipedia.org/"
             False, otherwise.
    '''
    return hyperlink=="https://en.wikipedia.org/wiki/Main_Page" or hyperlink=="https://www.wikipedia.org/"


def should_explore_link(hyperlink, anchor_text=None, keyword=None):
    '''
    check to see if the link should be explored.
    :param hyperlink: hyperlink
    :param anchor_text: anchor_text
    :param keyword: keyword
    :return: True, if the link should be explored,
             False, otherwise.
    '''
    return not (is_link_external(hyperlink)
                or is_link_visited(hyperlink)
                or is_link_administrative(hyperlink)
                or is_link_for_page_section(hyperlink)
                or is_link_pointing_to_main_page(hyperlink)) \
           and is_link_pointing_to_english_article(hyperlink) \
           and (is_keyword_satisfied(hyperlink, anchor_text, keyword)
                or is_compound_keyword(anchor_text, keyword))


def is_keyword_satisfied(hyperlink, anchor_text, keyword):
    '''
    If the keyword is None i.e. not set this function return True
    by default,
    But if the keyword is set then it check whether the anchor text
    or hyperlink matches the keyword.
    :param hyperlink: hyperlink
    :param anchor_text: anchor_text
    :param keyword: keyword
    :return: True if the anchor text or hyperlink matches keyword,
             False, otherwise.
    '''
    if keyword is not None:
        return is_anchor_text_satisfied_keyword(anchor_text, keyword) \
               or is_hyper_link_satisfied_keyword(hyperlink, keyword)
    return True


def is_anchor_text_satisfied_keyword(anchor_text, keyword):
    '''

    :param anchor_text: anchor_text
    :param keyword: keyword
    :return: True if the anchor text matches keyword,
             False, otherwise.
    '''
    for token in re.findall(r"[a-zA-Z0-9']+", "rain_rain"):
        if stemmer.stem(token) == keyword:
            return True
    return False


def is_hyper_link_satisfied_keyword(hyperlink, keyword):
    '''

    :param hyperlink: hyperlink
    :param keyword: keyword
    :return: True if the hyperlink matches keyword,
             False, otherwise.
    '''
    for token in re.findall(r"[a-zA-Z0-9']+", "rain_rain"):
        if stemmer.stem(token) == keyword:
            return True
    return False


def should_stop_crawling(frontier_item):
    '''

    :param frontier_item: frontier_item i.e. a link to a webpage.
    :return: True if the crawling should stop, i.e. when required
             depth has been reached or required URLs ahs been explored.
             False, otherwise.
    '''
    return frontier_item[FRONTIER_ITEM_DEPTH_INDEX] > MAXIMUM_CRAWL_DEPTH \
           or len(visited) >= UNIQUE_URL_THRESHOLD


def format_hyperlink(hyperlink):
    '''
    :param hyperlink: hyperlink element from beautiful soup
    :return:
            if the relative link start with "/wiki/"
            the function converts relative hyperlink to absolute
            with addition of "https://en.wikipedia.org".
            It also returns anchor text of the hyperlink.

            if the relative link doesn't start with "/wiki/"
            it return the same relative along with resolved anchor text.

    '''
    url = hyperlink['href']
    if url.startswith("/wiki/"):
        return hyperlink.getText(), "https://en.wikipedia.org" + url
    return hyperlink.getText(), url


def is_compound_keyword(compound_keyword, keyword):
    '''

    :param compound_word: compund keyword
    :param keyword: keyword
    :return: True in its compound keyword
             ex: rainbow if keyword is rain
             False, otherwise
    '''
    if keyword == None:
        return True
    if compound_keyword == "":
        return False

    compound_word_temp = compound_keyword.lower()
    keyword_temp = keyword.lower()
    keyword_index = compound_word_temp.find(keyword_temp)
    if keyword_index == -1 or keyword_index !=0:
        return False
    return compound_word_temp[keyword_index + len(keyword_temp):] in english_words_set




def internal_start_crawling(keyword=None):
    current_depth = 1
    previous_visit_time = 0
    for frontier_item in frontier:

        # terminate crawling
        if should_stop_crawling(frontier_item):
            return

        # Get all the required data from a frontier item
        anchor_text = frontier_item[FRONTIER_ITEM_ANCHOR_TEXT_INDEX]
        hyperlink = frontier_item[FRONTIER_ITEM_URL_INDEX]
        depth = frontier_item[FRONTIER_ITEM_DEPTH_INDEX]
        docid = frontier_item[FRONTIER_ITEM_DOC_ID_INDEX]

        # Truncating '#' part
        hyperlink = hyperlink if hyperlink.find('#')==-1 else hyperlink[:hyperlink.find('#')]


        # check to see if the hyperlink should be crawled.
        if should_explore_link(hyperlink):

            # politeness check                                      #time already elapsed
            time_to_sleep = POLITENESS_POLICY_DELAY_IN_SEC - (time.clock() - previous_visit_time)
            time.sleep(0 if time_to_sleep < 0 else time_to_sleep)

            # make note time
            previous_visit_time = time.clock()

            # open the link
            http_response = request.urlopen(hyperlink);

            # to handle redirects
            if not should_explore_link(http_response.geturl()):
                continue;

            # put link in visited
            visited[hyperlink] = frontier_item
            print("count:" + str(len(visited)) + " " + "depth:" + str(depth))

            # Get only content section HTML
            html_content_body = get_content_body(BeautifulSoup(http_response.read()))

            # Document the visited link
            document_link_and_content(len(visited), anchor_text, hyperlink, depth, current_depth != depth, html_content_body, docid)

            current_depth = depth
            # write_to_link_with_content(hyperlink, html_content_body)

            # Get all the hyper links in the content section
            for discovered_hyperlink in html_content_body.find_all('a', href=True):
                # format relative links to absolute links and get anchor text
                anchor_text, discovered_hyperlink = format_hyperlink(discovered_hyperlink)

                # check to see if the links should be explored
                if should_explore_link(discovered_hyperlink, anchor_text, keyword):
                    # if yes add the link to frontier
                    frontier.append((anchor_text, discovered_hyperlink, depth + 1, get_next_docid(), {frontier_item[FRONTIER_ITEM_DOC_ID_INDEX]}))

                elif is_link_visited(discovered_hyperlink):
                    visited[discovered_hyperlink][FRONTIER_ITEM_INLINK_SET_INDEX].add(frontier_item[FRONTIER_ITEM_DOC_ID_INDEX])



if __name__ == '__main__':
    start = time.clock()
    start_crawling(sys.argv[1])
    print("Time taken:"+str(time.clock() - start))

