import collections
import json
import os
import re

from exceptions import ShowNotFoundError, WatchlistNotFoundError


def sanitize_title(title):
    """Sanitize the title so that a valid API request can be made.

    Discards everything after the first ':' character and removes and '.'
    characters.

    Returns:
        lowercase version of the title.
    """
    # Discard everything after the colon
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


def tabulator(shows):
    """Tabulates and outputs a table of next episodes for each show in shows.

    Args:
        shows: List of TrackedShow instances

    Relevant attributes:
        TrackedShow.title: Title of the show
        TrackedShow.next.title Title of the episode
        TrackedShow.next.season
        TrackedShow.next.episode
    """
    padding = 3
    headers = ['Show', 'Next episode', 'Rating', 'Title']
    shows = sorted(shows)

    header_lengths = [len(h) for h in headers]
    max_show_title_length = max(len(s.title) for s in shows)
    max_ep_title_length = max(len(s._next.title) for s in shows)
    max_entry_lengths = [max_show_title_length, 6, 6, max_ep_title_length]
    column_widths = [max(h, e) for h, e in zip(header_lengths, max_entry_lengths)]

    # print()
    for header, width in zip(headers, column_widths):
        print('{:{}}{}'.format(header, width, ' '*padding), end='')
    print()

    for width in column_widths:
        print('{:-<{}}{}'.format('', width+1, (padding-1)*' '), end='')
    print()

    for show in shows:
        se_string = 'S{:02d}E{:02d}'.format(show._next.season, show._next.episode)

        if show._next.ratings['imdb'] is None:
            rating = 'N/A'
        else:
            rating = show._next.ratings['imdb']

        for field, w in zip((show.title, se_string, rating, show._next.title), column_widths):
            print('{:<{}}{}'.format(field, w, padding*' '), end='')
        print()


class ProcessWatchlist:
    """Read and process a list of shows being watched"""
    def __init__(self, path_to_watchlist=None):
        if path_to_watchlist is None:
            path_to_watchlist = 'watchlist.txt'

        self.path_to_watchlist = path_to_watchlist

    def __iter__(self):
        """Parses a text file of shows and next episodes.

        File should be in the following format:
        SHOW SEASONEPISODE [NOTES (if any)]

        Example:
        Game of Thrones S06E10 (Download 'Light of the Seven')

        Returns:
            namedtuple of shows currently being watched
        """
        try:
            with open(self.path_to_watchlist, 'r') as f:
                for line in f:
                    yield self.split_line(line.strip())
        except FileNotFoundError:
            raise WatchlistNotFoundError

    def split_line(self, line):
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
            ('show_title', 'next_episode', 'notes')
        )

        return NextEpisode(show, next_episode.upper(), notes)


def extract_episode_details(season, episode_response):
    """Clean and extract episode details response.

    Take an episode details response and cleans the data.
    Extract the relevant fields needed to construct an
    Episode object.

    Args:
        season: The season number
        episode_response: An episode_details response

    Returns:
        episode_details: Dictionary with relevant episode
            information
    """
    try:
        rating = float(episode_response['imdbRating'])
    except ValueError:
        # Rating may come through as 'N/A' if episode has not aired
        rating = None

    return {
        'title': episode_response['Title'],
        'episode': int(episode_response['Episode']),
        'season': season,
        'ratings': {'imdb': rating},
    }


def get_show_database_entry(show_database, title):
    """Get an entry in *show_database* for *title*.

    Args:
        show_database: A ShowDatabase instance.
        title: The lookup key for the show being searched for.

    Returns:
        A Show instance for show stored under *title*.

    Raises:
        ShowNotFoundError: Show not found in the passed in
            database.
    """
    try:
        return show_database._shows[title]
    except KeyError:
        raise ShowNotFoundError('Show <{!r}> not found in show database'.format(title))


def check_season_bounds(next_episode, show_details):
    """Check that an episode does not exceed the season bounds.

    Args:
        show_details: Show object with season and episode information.
            This comes from a ShowDatabase object.
        season:
        episode:

    Returns:
        x
    """
    pass


def check_file_exists(directory, filename):
    """Return True if a file exists, otherwise False"""

    path_to_file = os.path.join(directory, filename)

    if os.path.exists(path_to_file):
        return True

    return False


def check_for_databases(database_dir):
    """Check existence of Show Database and Tracker.

    Args:
        database_dir: directory containing databases

    Returns:
        Namedtuple with True/False flags based on whether
        or not the two databases exist.
    """
    showdb_exists = check_file_exists(database_dir, '.showdb.json')
    tracker_exists = check_file_exists(database_dir, '.tracker.json')

    DatabaseExistence = collections.namedtuple(
        'DatabaseExistence',
        ('showdb_exists', 'tracker_exists')
    )

    return DatabaseExistence(showdb_exists, tracker_exists)


def extract_season_episode_from_str(s):
    """Extract the season and episode from a string."""
    m = check_for_season_episode_code(s)

    if not m:
        return 1, 1

    return int(m.group(1)), int(m.group(2))


def check_for_season_episode_code(s):
    """Check if a season-episode code is present.

    Args:
        s: string

    Returns:
        m: regex match object if season-episode code present.
        False otherwise.
    """
    se_pattern = r'[sS](\d{1,2})[eE](\d{1,2})'

    m = re.search(se_pattern, s)

    if not m:
        return False

    return m


class Deserializer:
    def __init__(self, deserialized_data):
        self.deserialized_data = deserialized_data
        self.db = self._reconstruct_object(deserialized_data)

    def deserialize(self):
        """Construct a fully populated Database from deserialized_data."""
        for show, details in self.db._shows.items():
            self.db._shows[show] = self._reconstruct_object(details)
            self._populate_attributes(self.db._shows[show])
        return self.db

    def _populate_attributes(self, obj, traverse_list=True):
        """Populate attributes in *obj*.

        Iterate through the keys in the instance dict of *obj* and
        populate the attributes.

        After initial attribute population, check to see if the
        current attribute is a list. If so, then call this function
        again with a flag to indicate not to attempt a further
        recursion.

        Args:
            obj: An object
            traverse_list: Flag to indicate whether or not to recurse
        """
        for key, value in obj.__dict__.items():
            if isinstance(value, dict):
                obj.__dict__[key] = self._reconstruct_object(value)
            elif isinstance(value, list):
                obj.__dict__[key] = [self._reconstruct_object(details) for details in value]
                if traverse_list:
                    # Iterate through each season in the list of seasons
                    for season in obj.__dict__[key]:
                        self._populate_attributes(season, traverse_list=False)

    @staticmethod
    def _reconstruct_object(deserialized_data):
        """Reconstruct an object if the class has been registered.

        Check if the key in deserialized_data corresponds to a
        registered class and if so, construct and return an
        instance of the class with keyword arguments given in
        value in deserialized_data.

        Args:
            deserialized_data: dictionary of deserialized data

        Returns:
            an instance of a registered class
        """
        for key, value in deserialized_data.items():
            key = key.strip('__')
            if key in registry:
                # Gather the keyword arguments for class *key*
                kwargs = dict(value.items())
                return registry[key](**kwargs)


registry = {}


def register_class(target_class):
    registry[target_class.__name__] = target_class


class Meta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        register_class(cls)
        return cls


class RegisteredSerializable(metaclass=Meta):
    @classmethod
    def load(cls, **kwargs):
        return cls(**kwargs)


class EncodeShow(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, tuple(registry.values())):
            key = '__{}__'.format(obj.__class__.__name__)
            return {key: obj.__dict__}
        return json.JSONEncoder.default(self, obj)
