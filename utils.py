import collections
import re


def sanitize_title(title):
    """Sanitize the title so that a valid API request can be made.

    Discards everything after the first ':' character and removes and '.'
    characters.

    Returns:
        lowercase version of the title.
    """
    # Discard everything after the title
    title = title.split(':')[0]
    title.replace('.', '')
    return title.lower()


def titleize(title):
    """Return a correctly capitalised show title.

    Usage:
    >>> print(titleize('the cat in the hat'))
    >>> 'The Cat in the Hat'
    """
    titleized = []
    for idx, word in enumerate(title.split()):
        if idx == 0 or word not in ['a', 'of', 'in', 'the', 'v']:
            word = word.capitalize()

        titleized.append(word)

    return ' '.join(titleized)


def lunderize(title):
    """Returns a lowercase, underscored representation of a string.

    Usage:
    >>> print(lunderize('The Cat in the Hat'))
    >>> 'the_cat_in_the_hat'
    """
    title = title.lower()
    title = title.replace(' ', '_')
    title = title.replace('.', '')
    return title

def parse_watch_list(path_to_file):
    """Parses a text file of shows and next episodes.

    File should be in the following format:
    SHOW SEASONEPISODE [NOTES (if any)]

    Example:
    Game of Thrones S06E10 (Download 'Light of the Seven')

    Returns:
        namedtuple of shows currently being watched
    """
    with open(path_to_file, 'r') as f:
        for line in f:
            yield split_line(line)


def split_line(line):
    """Split an input line into a show, the next episode and notes (if any).

    Expects a line in the following form:
        Game of Thrones S05E09
    """
    notes = None
    # Optional notes can be added, so split on a bracket or paren
    line = re.split(r'[\[\(]', line)

    if len(line) > 1:
        details, notes = line
        notes = notes[:-1]  # Strip out the trailing bracket or paren
    else:
        details = line[0]

    show, next_episode = details.rstrip().rsplit(maxsplit=1)

    NextEpisode = collections.namedtuple(
        'NextEpisode',
        ('show', 'next_episode', 'notes')
    )

    return NextEpisode(show, next_episode, notes)


def get_season_episode_from_str(s):
    """Extract a season and episode from a string.

    Usage:
        get_season_episode_from_str('S06E10')
    """
    pattern = r'\w{1}(\d{1,2})'*2
    m = re.search(pattern, s)
    # TODO: Refactor this out
    if not m:
        raise SeasonEpisodeParseError

    season = int(m.group(1))
    episode = int(m.group(2))
    return season, episode
