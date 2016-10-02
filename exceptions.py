class ShowDatabaseError(Exception):
    pass


class ShowNotFoundError(ShowDatabaseError):
    pass


class WatchlistNotFoundError(ShowDatabaseError):
    pass


class DatabaseNotFoundError(ShowDatabaseError):
    pass


class FoundFilmError(ShowDatabaseError):
    pass


class TrackerError(Exception):
    pass


class ShowNotTrackedError(TrackerError):
    pass


class SeasonEpisodeParseError(TrackerError):
    pass


class OutOfBoundsError(TrackerError):
    pass


class EpisodeOutOfBoundsError(OutOfBoundsError):
    pass


class SeasonOutOfBoundsError(OutOfBoundsError):
    pass


class InvalidOperationError(Exception):
    pass

class DatabaseError(Exception):
    pass

class TrackerDatabaseNotFoundError(DatabaseError):
    pass

class ShowDatabaseNotFoundError(DatabaseError):
    pass

class InvalidUsageError(Exception):
    pass