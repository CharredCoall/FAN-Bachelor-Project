import numpy as np
import csv
import pandas as pd




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



def run_iia():

    part1 = csv.reader(open("merged_dataset_part1.csv", mode='r', encoding='Latin-1'))
    part2 = csv.reader(open("merged_dataset_part2.csv", mode='r', encoding='Latin-1'))

    next(part1, None)
    next(part2, None)

    N1 = len(np.fromiter(part1, dtype=np.ndarray))
    N2 = len(np.fromiter(part2, dtype=np.ndarray))

    M = np.zeros((N1 + N2,3))

    for an in ["asger", "Franja", "natali"]:
        i = 0
        for part in [1,2]:
            with open(f"{an}/merged_dataset_part{part}_{an}.csv", mode='r', encoding='Latin-1') as path:
                file = csv.reader(path)
                next(file, None)
                for row in file:
                    if row[-1] != '':
                        M[i,int(row[-1])-1] += 1
                        i += 1 

    M = M[~np.all(M == 0, axis=1)]

    print(fleiss_kappa(M))


if __name__ == "__main__":
    run_iia()