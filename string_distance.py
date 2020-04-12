import numpy as np


def levenshtein_distance(string1, string2):
    m, n = len(string1), len(string2)
    matrix = np.zeros((m + 1, n + 1), dtype=np.int32)

    # source prefixes can be transformed into empty string by
    # dropping all characters
    for i in range(m + 1):
        matrix[i, 0] = i

    # target prefixes can be reached from empty source prefix
    # by inserting every character
    for j in range(n + 1):
        matrix[0, j] = j

    for j in range(n + 1):
        for i in range(m + 1):
            if string1[i - 1] == string2[j - 1]:
                substitution_cost = 0
            else:
                substitution_cost = 1

            matrix[i, j] = min(matrix[i - 1, j] + 1,  # deletion
                               matrix[i, j - 1] + 1,  # insertion
                               matrix[i - 1, j - 1] + substitution_cost)  # substitution

    return matrix[m, n]
