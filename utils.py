import collections
import re

from exceptions import SeasonEpisodeParseError


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


class ProcessWatchlist:
    """Read and process a list of shows being watched"""
    def __init__(self, path_to_watchlist='./watchlist.txt'):
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
        with open(self.path_to_watchlist, 'r') as f:
            for line in f:
                yield self.split_line(line.strip())

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
            ('show', 'next_episode', 'notes')
        )

        return NextEpisode(show, next_episode, notes)


# TODO: This function is now a method in the tracker module
# Move the tests associated with this
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
                return registry[key].load(**kwargs)


registry = {}


class Meta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        register_class(cls)
        return cls


class RegisteredSerializable(metaclass=Meta):
    pass


def register_class(target_class):
    registry[target_class.__name__] = target_class
