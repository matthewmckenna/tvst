# Script to parse next_episode.txt
# C:\Users\Matthew\Dropbox\Matthew\notes\next_episode.txt
# next_episode
#
# Mon 27/06/2016 15:50 IST
#
# The Blacklist S03E09
# Daredevil S01E03 (S01E02 with Claire)
# Game of Thrones S06E10
# Sons of Anarchy S01E02 (with Claire)
#
# Rewatch:
# Dexter S02E03 ?
#
# Seasons not-yet-started:
# Fargo S02E01
# Person of Interest S05E01
#
# x AHS S06E01
# x Homeland S06E01
# x Making a Murderer
# x Mr. Robot S02E01 (~June/July 2016)
# x Supernatural S12E01 (October 13 2016)
#
# My List:
# 11/22/63
# American Crime Story: The People v OJ Simpson
# The Bridge (Danish)
# House of Cards (British)

# words not to capitalise = ['a', 'of', 'in', 'the', 'v']
# capitalise if at the start of a sentence = ['A', 'The']
import string

def titleise(title):
    """Return a correctly capitalised show title.

    Usage:
    >>> print(titleise('the cat in the hat'.split()))
    >>> 'The Cat in the Hat'
    """
    titleised = []
    for idx, word in enumerate(title):
        if idx == 0 or word not in ['a', 'of', 'in', 'the', 'v']:
            word = word.capitalize()

        titleised.append(word)

    return ' '.join(titleised)


def lunderise(title):
    """Returns a lowercase, underscored representation of a string.

    Usage:
    >>> print(lunderise('The Cat in the Hat'.split()))
    >>> 'the_cat_in_the_hat'
    """
    title = title.lower()
    title = title.replace('.', '')
    title = title.replace(':', '')
    title = title.replace(' ', '_')
    title = title.replace('/', '_')

    return title


if __name__ == '__main__':
    title = 'the cat in the hat'
    title = 'mr robot'
    title = 'american crime story: the people v oj simpson'
    # TODO: Rule for after a colon :
    # TODO: Rule for a name like OJ
    print(titleise(title.split()))
    # print(' '.join(titleise(title.split())))
    # print()
