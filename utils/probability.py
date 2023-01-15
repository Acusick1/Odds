import numpy as np


def combined_odds(odds: np.array) -> float:

    prob = odds2probs(odds).sum()
    return probs2odds(prob)


def odds2probs(odds: np.array) -> np.array:

    return 1./(odds + 1)


def probs2odds(probs: np.array) -> np.array:

    return 1./probs - 1


if __name__ == "__main__":

    stake = 100
    book1_odds = np.array([1/3, 4, 13/2, 66, 500])
    book2_odds = np.array([1/2, 5, 6, 100, 200])

    all_odds = np.vstack([book1_odds, book2_odds])

    ids = all_odds.argmax(axis=0)
    odds_arr = np.max(all_odds, axis=0)

    prob_arr = odds2probs(odds_arr)
    stake_arr = stake * prob_arr/prob_arr.sum()
    stake_dict = [{"book": book_id, "stake": s} for book_id, s in zip(ids, stake_arr)]

    print("Summed probabilities", prob_arr.sum())
    print("Probabilities: ", prob_arr)
    print("Stakes: ", stake_dict)
    print("Returns: ", min((stake_arr * odds_arr) + stake_arr))
