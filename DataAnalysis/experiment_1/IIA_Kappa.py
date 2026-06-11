import numpy as np
import csv


def fleiss_kappa(M):
    """Computes Fleiss' kappa for group of annotators.
    :param M: a matrix of shape (:attr:'N', :attr:'k') with 'N' = number of subjects and 'k' = the number of categories.
        'M[i, j]' represent the number of raters who assigned the 'i'th subject to the 'j'th category.
    :type: numpy matrix
    :rtype: float
    :return: Fleiss' kappa score
    """
    N, k = M.shape  # N is # of items, k is # of categories
    n_annotators = float(np.sum(M[0, :]))  # # of annotators
    tot_annotations = N * n_annotators  # the total # of annotations
    category_sum = np.sum(M, axis=0)  # the sum of each category over all items

    # chance agreement
    p = category_sum / tot_annotations  # the distribution of each category over all annotations
    PbarE = np.sum(p * p)  # average chance agreement over all categories

    # observed agreement
    P = (np.sum(M * M, axis=1) - n_annotators) / (n_annotators * (n_annotators - 1))
    Pbar = np.sum(P) / N  # add all observed agreement chances per item and divide by amount of items

    return round((Pbar - PbarE) / (1 - PbarE), 4)

def weighted_kappa(M):

    N, q = M.shape # N is # of items, q is # of categories
    w = 1 - ((np.subtract.outer(np.arange(q),np.arange(q))) ** 2) / (q-1) ** 2 #Quadratic weights for the scale 0-2
    r = np.sum(M, axis=1) # r is the number of raters that assigned item i to any category

    r_star = np.zeros((N,q))
    p_o_prime = 0
    r_bar = np.mean(r)
    epsilon = 1/(N*r_bar)
    p_o = 0
    pi = np.zeros(q)
    p_c = 0

    for i in range(N):
        for k in range(q):
            r_star[i,k] = np.dot(w[k], M[i])

    for i in range(N):
        for k in range(q):
            p_o_prime += (M[i,k] * (r_star[i,k] - 1)) / (r_bar * (r[i] - 1))

    p_o_prime /= N

    p_o = p_o_prime * (1-epsilon) + epsilon    

    pi = np.mean(M/r_bar,  axis=0)

    for k in range(q):
        for l in range(q):
            p_c += w[k,l] * pi[k] * pi[l]


    return round((p_o-p_c)/(1-p_c) ,4)



def run_iia():

    #Combine datasets into Score matrix
    part1 = csv.reader(open("merged_dataset_part1.csv", mode='r', encoding='Latin-1'))
    part2 = csv.reader(open("merged_dataset_part2.csv", mode='r', encoding='Latin-1'))

    next(part1, None)
    next(part2, None)

    N1 = len(np.fromiter(part1, dtype=np.ndarray))
    N2 = len(np.fromiter(part2, dtype=np.ndarray))

    M = np.zeros((N1 + N2,3))

    #Iterate over all raters
    for an, suf in [("asger/", "_asger"), ("franja/", "_franja"), ("natali/", "_natali"), ("judge_", "")][:2]:
        i = 0
        for part in [1,2]:
            with open(f"{an}merged_dataset_part{part}{suf}.csv", mode='r', encoding='Latin-1') as path:
                file = csv.reader(path)
                next(file, None)
                #Count scores of all rows 
                for row in file:
                    if row[-1] != '': #Ignore if no score was given
                        M[i,int(row[-1][0])-1] += 1
                        i += 1 

    M = M[np.sum(M, axis=1) > 2] #Remove rows where not everyone scored

    #Calculate and report fleiss kappa and kirpendorfs alpha 
    print("Fleiss' Kappa:", fleiss_kappa(M))
    print("Kripendorff's Alpha:", weighted_kappa(M))


if __name__ == "__main__":
    run_iia()