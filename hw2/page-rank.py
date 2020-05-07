import collections
import math

# Name of the graph file to load
GRAPH_FILE_NAME = "G1.txt"

# Translation file to translate from document-id to URL
# Should be of the form ex:For G1 it should be G1_LINKS.txt
G_LINKS_FILE = GRAPH_FILE_NAME[:GRAPH_FILE_NAME.index(".")]+"_"+"LINKS"+".txt"

# Output file for top N ranks to be filtered
TOP_N_PAGERANKS = -50;

# Output file for top TOP_N_PAGERANKS page ranks
PR_OUTPUT_FILE_NAME = "TOP_"+str(TOP_N_PAGERANKS)+"_PAGERANKS_"+GRAPH_FILE_NAME[:GRAPH_FILE_NAME.index(".")]+".txt"

# Output file for top TOP_N_PAGERANKS inlink ranks
INLINKS_OUTPUT_FILE_NAME = "TOP_"+str(TOP_N_PAGERANKS)+"_INLINKS_"+GRAPH_FILE_NAME[:GRAPH_FILE_NAME.index(".")]+".txt"

# Output statistics for GRAPH_FILE_NAME
STATS_OUTPUT_FILE_NAME = GRAPH_FILE_NAME[:GRAPH_FILE_NAME.index(".")]+"_STATS.txt"

# P is the set of all pages.
P = set()

# S is the set of sink nodes, i.e., pages that have no out links.
S = set()

# M is the dictionary. with key as page p, with the value as that set of links to page p
# M[p] is the set (without duplicates) of pages that link to page p
M = dict()

# L is the dictionary. with key as page q, with the value as number of out-links from the page q
# L[q] is the number of out-links from page q
L = dict()

# Number of pages. |P| = N
N = 0

# d is the PageRank damping/teleportation factor; use d = 0.85 as a fairly typical value
d = 0.85

# PR is page rank dictionary, which as page as key and pagerank as value.
PR = dict()


def read_graph_file():
    '''
    Reads the the graph from the file GRAPH_FILE_NAME
    and loads and pre-computes necessary information
    requires to calculate PageRank.
    :return: None
    '''
    with open(GRAPH_FILE_NAME, 'r', encoding="utf-8") as graph_file:
        # Accessing global variables
        global S, N, P
        for vertex_item in graph_file:
            vertex_tokens = vertex_item.strip().split(" ")
            page, in_links = vertex_tokens[0], vertex_tokens[1:]

            # add page to pages
            P.add(page)

            # store info about page vs in-links
            M[page] = set(in_links)

            # update L i.e. page vs out-link count
            update_outlink_count_for_page(L, in_links)

        # Set of all the pages that have not entry in L(out-link dict). Are the sink nodes.
        S = P - L.keys()

        # Calculate value of N
        N = len(P)

doc_to_links={}

def read_doc_translation_file():
    '''
    Reads the G*_LINKS_FILE which helps
    from translating DocId to URL
    :return: None
    '''
    try:
        with open(G_LINKS_FILE, 'r', encoding="utf-8") as graph_file:
            for vertex_item in graph_file:
                vertex_tokens = vertex_item.strip().split("|")
                if len(vertex_tokens)==1: continue
                doc_to_links[vertex_tokens[1]] = vertex_tokens[len(vertex_tokens)-1]
    except:
        print("G_LINKS_FILE not found!")




def update_outlink_count_for_page(L, in_links):
    '''
    updates all the out-link counts by one of pages in L,
    for all the pages present in in_links.
    :param L: dict of page vs out-link count
    :param in_links: current in-links to page
    :return: None
    '''
    for in_link in in_links:
        if in_link in L:
            L[in_link] += 1
        else:
            L[in_link] = 1


def calculate_entropy(PR):
    '''
    Calculates the entropy of values in PR dictionary(page-ranks).
    :param PR: PageRank dictionary
    :return: entropy of PR
    '''
    entropy = 0
    for pr in PR.values():
        entropy += pr * math.log2(pr)
    return - entropy


def calculate_perplexity(PR):
    '''
    Calculates the perplexity of values in PR dictionary(page-ranks).
    :param PR: PageRank dictionary
    :return: perplexity of PR
    '''
    return pow(2, calculate_entropy(PR))


# Queue to store perplexity values of lat 4 iterations
PR_records = collections.deque(maxlen=4)


def is_page_rank_converged(PR, tolerance=1):
    '''
    Performs convergence check using last 4 iteration of PageRank values
    :param PR: PageRank dictionary
    :param tolerance: tolerance check for convergence
    :return: True if four iterations of PR have perplexity
             value within the tolerance.
             False otherwise.
    '''
    perplexity = calculate_perplexity(PR)
    print("Perplexity = "+str(perplexity))
    PR_records.append(perplexity)

    # to make sure at least 4 iteration are done
    if len(PR_records) < 3:
        return False

    for i in range(len(PR_records)):
        for k in range(i, len(PR_records)):
            # if difference is > tolerence return false
            if abs(PR_records[i] - PR_records[k]) > tolerance:
                return False
    return True

def write_PR_to_file(top=TOP_N_PAGERANKS):
    '''
    Writes top TOP_N_PAGERANKS pageranks into file.
    :param top: top
    :return: None
    '''
    with open(PR_OUTPUT_FILE_NAME, 'w', encoding="utf-8") as pr_output_file:
        for pr_item in sorted(PR.items(), key=lambda x:x[1], reverse=True )[top:]:
            pr_output_file.write(str(pr_item[0])+"|"+str(pr_item[1])+"|"+ doc_to_links.get(pr_item[0],""))
            pr_output_file.write("\n")


def write_inlinks_to_file(top=TOP_N_PAGERANKS):
    '''
    Writes top TOP_N_PAGERANKS inlinks into file.
    :param top: top
    :return: None
    '''
    with open(INLINKS_OUTPUT_FILE_NAME, 'w', encoding="utf-8") as pr_output_file:
        for pr_item in sorted(M.items(), key=lambda x:len(x[1]), reverse=True )[top:]:
            pr_output_file.write(str(pr_item[0])+"|"+str(len(pr_item[1])) +"|"+ doc_to_links.get(pr_item[0],""))
            pr_output_file.write("\n")

def write_stats_to_file():
    '''
    Writes stats of graph into file.
    :return: None
    '''
    with open(STATS_OUTPUT_FILE_NAME, 'w', encoding="utf-8") as stats_output_file:
        stats_output_file.write("Number of Documents: "+ str(len(P)))
        stats_output_file.write("\n")
        stats_output_file.write("Number of Documents without in-links: " +
                                str(len([x for x in M.items() if len(x[1])==0])))
        stats_output_file.write("\n")
        stats_output_file.write("Number of Documents without out-links: " +str(len(S)))
        stats_output_file.write("\n")




def page_rank():
    '''
    Calculates the PageRank of the Graph.
    :return: None
    '''

    # accessing global PR dictionary.
    global PR

    # Initializing values for PR.
    for p in P:
        PR[p] = 1 / N

    # Initializing iteration counter.
    iteration = 0

    # loop util PageRank not converged
    while not is_page_rank_converged(PR):

        # Incrementing iteration counter by 1
        iteration += 1

        # Initializing sinkPR.
        sinkPR = 0

        # Initializing newPR.
        newPR = dict()

        # calculate total sinkPR
        for p in S:
            sinkPR += PR[p]

        for p in P:

            # teleportation value calculation
            newPR[p] = (1 - d) / N

            # spread remaining sinkPR evenly
            newPR[p] += d * (sinkPR / N)

            # pages pointing to p
            for q in M[p]:
                # add share of PageRank from in‐links
                newPR[p] += d * (PR[q] / L[q])

        # update PR with newPR
        for p in P:
            PR[p] = newPR.get(p)

    print("Number of iteration : "+str(iteration))


if __name__ == '__main__':
    read_graph_file()
    read_doc_translation_file()
    page_rank()
    write_PR_to_file()
    write_inlinks_to_file()
    write_stats_to_file()

