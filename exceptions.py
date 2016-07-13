class ShowDatabaseError(Exception):
    pass


class ShowNotFoundError(ShowDatabaseError):
    pass

class FoundFilmError(ShowDatabaseError):
    pass


class TrackerError(Exception):
    pass


class ShowNotTrackedError(TrackerError):
    pass


class SeasonEpisodeParseError(TrackerError):
    pass
