# encoding: utf-8

LETTER_VALUE = {}
LETTER_VALUE.update({
    l: 1 for l in set('aedgilonsrut')
})
LETTER_VALUE.update({
    l: 2 for l in set('cbfhmpwvy')
})
LETTER_VALUE.update({
    l: 3 for l in set('qxkzj')
})

assert len(LETTER_VALUE.keys()) == 26


def get_word_score_value(word):
    return sum([LETTER_VALUE[l] for l in word])


def add_new_longest_word(longest_words, word, max_longest):
    word_len = len(word)
    if len(longest_words) >= max_longest:
        for pos in xrange(len(longest_words)):
            if len(longest_words[pos]) < word_len:
                longest_words.pop(pos)
                break

    longest_words.append(word)
    min_word_length = min([len(x) for x in longest_words])

    return min_word_length, longest_words


def add_new_scoring_word(scoring_words, word, max_scoring):
    word_score = get_word_score_value(word)
    if len(scoring_words) >= max_scoring:
        for pos in xrange(len(scoring_words)):
            if get_word_score_value(scoring_words[pos]) < word_score:
                scoring_words.pop(pos)
                break

    scoring_words.append(word)
    min_word_score = min([get_word_score_value(x) for x in scoring_words])

    return min_word_score, scoring_words


def find_bruteforce(letter_list, word_list, max_longest=1, max_scoring=1):
    longest_words = []
    scoring_words = []
    min_word_length = 0
    min_word_score = 0

    letter_counts = dict(
        [(x.lower(), letter_list.count(x)) for x in set(letter_list)]
    )

    for word in word_list:
        if any([word.count(l) > letter_counts.get(l, 0) for l in set(word)]):
            continue

        if len(word) > min_word_length:
            min_word_length, longest_words = add_new_longest_word(longest_words, word, max_longest)

        if get_word_score_value(word) > min_word_score:
            min_word_score, scoring_words = add_new_scoring_word(scoring_words, word, max_scoring)
    
    return longest_words, scoring_words


def print_words(words):
    words = sorted([(len(x), get_word_score_value(x), x) for x in words], key=lambda x: x[0])
    print words


if __name__ == "__main__":
    letter_lists = [
        ['G', 'E', 'E', 'A', 'I', 'W', 'T', 'I', 'N', 'E', 'E', 'V', 'Q', 'O', 'N'],
        ['G', 'T', 'A', 'N', 'E', 'X', 'E', 'A', 'U', 'I', 'E', 'H', 'T', 'D', 'E'],
        ['O', 'R', 'U', 'T', 'N', 'D', 'Y', 'B', 'E', 'C', 'G', 'F', 'J', 'R', 'S'],
        ['E', 'Q', 'N', 'D', 'P', 'E', 'V', 'L', 'M', 'E', 'E', 'X', 'Y', 'E', 'O'],
    ]

    with open('words.txt', 'rb') as input:
        word_list = map(lambda x: x.strip(), input.readlines())

    for ll in letter_lists:
        print ll
        top_length, top_score = find_bruteforce(ll, word_list, 3, 3)
        print_words(top_length)
        print_words(top_score)
