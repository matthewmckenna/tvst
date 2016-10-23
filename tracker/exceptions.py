"""This module contains exceptions for the TVST application."""


class APIRequestError(Exception):
    """Base exception class for errors raised when dealing with external API"""


class FoundFilmError(APIRequestError):
    """A film was found with the same name as the requested show."""


class ShowNotFoundError(APIRequestError):
    """The requested show was not found in the external database."""


class TrackerError(Exception):
    """Base class for errors relating to the Tracker database."""


class ShortCodeAlreadyAssignedError(TrackerError):
    """Raised when user tries to use a short-code which has already been assigned."""


class ShowAlreadyTrackedError(TrackerError):
    """The show already exists in the Tracker database."""


class ShowNotTrackedError(TrackerError):
    """Raised when action is requested on a show that is not tracked, e.g., incrementing
    the next episode for a show which does not exist in the Tracker database.
    """

class ParserError(Exception):
    """Base excpetion class to catch any errors relating to parsing user input."""


class SeasonEpisodeParseError(ParserError):
    """Raised when an error is encountered parsing a season-episode code string."""


class OutOfBoundsError(Exception):
    """Base exception class for indexing into season or episode list structures."""


class EpisodeOutOfBoundsError(OutOfBoundsError):
    """Raised when trying to access an invalid episode, e.g., episode 99 of
    a 10 episode season.
    """


class SeasonOutOfBoundsError(OutOfBoundsError):
    """Raised when trying to access an invalid season, e.g., season 7 of
    a 2 season show.
    """


class DatabaseError(Exception):
    """Base class dealing with database errors."""


class TrackerDatabaseNotFoundError(DatabaseError):
    """Raised when the Tracker database cannot be found."""


class ShowDatabaseNotFoundError(DatabaseError):
    """Raised when the show database cannot be found."""


class InvalidUsageError(Exception):
    """Base exception class to catch invalid usage of the application."""


class WatchlistError(Exception):
    """Base expction class which is concerned with errors relating to the watchlist."""


class EmptyFileError(WatchlistError):
    """Raised when the watchlist passed is empty."""


class WatchlistNotFoundError(WatchlistError):
    """Raised when a watchlist cannot be found."""
