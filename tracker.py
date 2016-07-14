#!/usr/env/python
"""
Utility to keep track of TV shows
"""
# import argparse
import datetime
import json
# import logging
import os
import re
import sys

import requests

# from utils import ToDictMixin, JSONMixin  # TODO: Move these classes
from exceptions import (
    SeasonEpisodeParseError,
    ShowNotFoundError,
    ShowNotTrackedError,
    FoundFilmError,
)
from utils import (
    Deserializer,
    EncodeShow,
    extract_episode_details,
    lunderize,
    ProcessWatchlist,
    RegisteredSerializable,
    sanitize_title,
    titleize,
)

# TODO: Add command line arguments
# TODO: Add logging
# TODO: Should a show be an object?
# TODO: Retrieve IMDB ratings
# TODO: Retrieve IGN ratings
# TODO: Retrieve episode synopsis


class Season(RegisteredSerializable):
    """Represent a season of a TV show"""
    def __init__(self, episodes_this_season=0, _episodes=None):
        self._episodes = [] if _episodes is None else _episodes
        self.episodes_this_season = 0 if episodes_this_season is None else len(self._episodes)

    def add_episode(self, episode):
        """Add an episode object to self._episodes"""
        self._episodes.append(episode)

    def construct_episode(self, episode_details):
        return Episode(**episode_details)

    def build_season(self, details):
        """Build a season of episodes"""
        season = int(details['Season'])
        for episode in details['Episodes']:
            # ep = self.construct_episode(season, episode)
            episode_details = extract_episode_details(season, episode)
            self.add_episode(self.construct_episode(episode_details))

        # Update the number of episodes this season
        self.episodes_this_season = len(self._episodes)

    def __getitem__(self, index):
        return self._episodes[index]

    def __iter__(self):
        return iter(self._episodes)

    def __len__(self):
        return len(self._episodes)


class Episode(RegisteredSerializable):
    def __init__(self, episode, season, title, ratings):
        self.episode = episode
        self.season = season
        self.title = title
        self.ratings = ratings

    def __repr__(self):
        return '< {self.title} (S{self.season:02d}E{self.episode:02d}) >'.format(
            self=self
        )


class ShowDetails(RegisteredSerializable):
    """Provide basic information about a show.

    Provide access to various title formats and the short_code of
    a Show.
    """
    def __init__(self, title=None, short_code=None):
        self.title = title
        self.request_title = sanitize_title(title)
        self.ltitle = lunderize(title)
        self.short_code = short_code


class TrackedShow(ShowDetails):
    """Keep track of next and previous episodes of a tracked show.

    Available methods:
        inc_episode
    """
    def __init__(self, title=None, next_episode=None, notes=None, short_code=None):
        super().__init__(title, short_code)
        self.next = None
        self.notes = notes
        self.previous = None
        self._next_episode = next_episode

    def _get_season_episode_from_str(self):
        """Extract a season and episode from a string."""
        pattern = r'\w{1}(\d{1,2})'*2
        m = re.search(pattern, self._next_episode)

        if not m:
            raise SeasonEpisodeParseError

        season = int(m.group(1))
        episode = int(m.group(2))
        return season, episode

    def inc_episode(self):
        raise NotImplementedError


class Show(ShowDetails):
    """Represent various details of a show.

    Available attributes:
        next
    """
    def __init__(self, title=None, short_code=None, _seasons=None):
        super().__init__(title, short_code)
        self._seasons = [] if _seasons is None else _seasons

    def request_show_info(self, season=None):
        """Make API request with season information"""
        if season:
            payload = {'t': self.request_title, 'season': season}
        else:
            payload = {'t': self.request_title}

        with requests.Session() as s:
            response = s.get('http://www.omdbapi.com', params=payload)

        response.raise_for_status()

        # TODO: Add error checking to response object
        return response.json()

    def populate_seasons(self, update_title=True):
        # IO
        show_details = self.request_show_info()

        # Response value is returned as a string
        if show_details['Response'] == 'False':
            raise ShowNotFoundError

        # We got a film of the same name
        if show_details['Type'] == 'movie':
            raise FoundFilmError

        total_seasons = int(show_details['totalSeasons'])

        # IO
        for season in range(1, total_seasons+1):
            season_details = self.request_show_info(season=season)
            self.add_season(season_details)

        # TODO: Wrong place to do this
        # Update the show title
        if update_title:
            self.title = season_details['Title']

    def add_season(self, season_details):
        s = Season()
        s.build_season(season_details)
        self._seasons.append(s)


class Database(RegisteredSerializable):
    """Provide base method for different types of databases"""
    def __init__(self, database_dir=None, watchlist_path=None):
        if database_dir is None:
            database_dir = os.path.join(os.path.expanduser('~'), '.showtracker')
        self._database_dir = database_dir

        watchlist_path = './watchlist.txt' if watchlist_path is None else watchlist_path
        self._watchlist_path = watchlist_path

        # TODO: Bad idea to do this in the init
        self.watchlist = self.read_watchlist()

        # Create a directory for the databases to live
        try:
            os.mkdir(self._database_dir)
        except OSError:
            pass  # TODO: Log that the directory already exists

    def load_database(self):
        """Return an existing database"""
        with open(self.path_to_database, 'r') as db:
            deserialized_data = json.load(db)

        deserializer = Deserializer(deserialized_data)
        database = deserializer.deserialize()

        return database._shows

    def write_database(self):
        """Write a ShowDatabse to disk"""
        date_format = '%A %B %d, %Y %H:%M:%S'
        self.last_modified = datetime.datetime.now().strftime(date_format)

        with open(self.path_to_database, 'w', encoding='utf-8') as f:
            json.dump(self, f, cls=EncodeShow, indent=2, sort_keys=True)

    def read_watchlist(self):
        try:
            watchlist = ProcessWatchlist(self._watchlist_path)
        except WatchlistNotFoundError


class ShowDatabase(Database):
    def __init__(self, database_dir=None, watchlist=None):
        super().__init__(database_dir, watchlist)
        self._shows = {}
        self.path_to_database = os.path.join(self._database_dir, '.showdb.json')
        self.last_modified = None

        if os.path.exists(self.path_to_database):
            self._shows = self.load_database()
        else:
            self.create_database()

    # TODO: Refactor this method
    def add_show(self, show_title):
        # TODO
        show = Show(show_title)
        # FIXME: Hidden IO
        try:
            show.populate_seasons()
        except FoundFilmError:
            # TODO: Handle this properly
            # Current idea is to go to imdb.com, do a search with request_title
            # Then scrape the response page for *SHOW* (TV Series).
            # Extract the IMDB ID and then perform another search on
            # omdbapi.com with the direct ID
            print('Film found with the same name. Try adding a year with request.')
        else:
            self._shows[show.ltitle] = show

    def create_database(self):
        """Create a show database."""
        for show in self.watchlist:
            # TODO: Refactor to just pass show to add_show()
            self.add_show(show.show_title)


# supernatural._seasons[0]._episodes[0].rating['imdb']
# supernatural.next.
    # def update(self, from_file=True):
    #     if from_file:
    #         self.next['season'], self.next['episode'] = show_update()


# read next_episode.txt
# compile a list of shows
# for show in shows: show should be lunderised
# init

# game_of_thrones = Show('Game of Thrones')
# query = 'game of thrones'
# show = getattr(sys.modules[__name__], query)
def test_update_database():
    shows = ['Game of Thrones', 'Silicon Valley']
    show_db = ShowDatabase()
    for show in shows:
        show_db.add_show(Show(show))

    with open('db_test.json', 'w') as f:
        json.dump(show_db, f, cls=EncodeShow, indent=2, sort_keys=True)


def create_tracker(path_to_file):
    """Create a Tracker object."""
    tracker = Tracker()
    for show in tracked_shows:
        tracker.add(
            TrackedShow(
                title=show.title,
                next_episode=show.next_episode,
                notes=show.notes,
            )
        )
    return tracker


def update_tracker_title(tracker, database):
    """Update the title attribute in the tracker with those from
    the ShowDatabase.
    """
    for show in tracker:
        show.title = database[show.ltitle]['title']


class TrackerDatabase(Database):
    """Provided methods to read current tracker information.

    Available methods:
        next_episode:
    """
    def __init__(self, database_dir=None):
        super.__init__(database_dir)
        self.path_to_database = os.path.join(self._database_dir, '.tracker.json')
        self._shows = {}

        if os.path.exists(self.path_to_database):
            # Perhaps we should do the load in init?
            self._db = self.load_database()
            self.construct_tracker()
        else:
            self.create_tracker()

    def create_tracker(self):
        """Create a tracker if it does not already exist"""
        watchlist = ProcessWatchlist(self._watchlist)
        for show in watchlist:
            self.add(show)

    def add(self, show):
        tracked_show = TrackedShow(
            title=show.title,
            next_episode=show.next_episode,
            notes=show.notes,
        )
        self._shows[tracked_show.ltitle] = tracked_show

    def add_next_prev_episode(self, database):
        """Add the next and previous episodes for the tracked show"""
        for show in self._shows:
            season, episode = show._get_season_episode_from_str(show._next_episode)
            season = database._shows[show.ltitle][season-1][episode-1]
            database._shows['game_of_thrones']._seasons[1]._episodes[1].title
            database._shows['game_of_thrones']['_seasons'][1]['_episodes'][1]
            try:
                season = database[show.ltitle][season-1]
            except IndexError:
                print('Season out of bounds')

            try:
                episode = season[episode-1]
            except:
                episode = x

    # TODO: Make this function work for next and previous episode
    def get_episode_details(self, show, verbose=False, which='next'):
        """Return the next episode for the show provided."""
        try:
            details = self.tracker['shows'][show]
        except KeyError:
            raise ShowNotTrackedError

        try:
            details = details[which]
        except KeyError:
            return 'No {} episode information available'.format(which)

        if verbose:
            msg = ''.join('{}: {}\n'.format(key.capitalize(), value) for key, value in details.items())
        else:
            msg = '{} episode for {}: S{:02d} E{:02d}'.format(
                which.capitalize(),
                titleize(show.split()),
                details['season'],
                details['episode'],
            )

        return msg

    def inc_episode(self, show):
        """Increment the current episode number."""
        try:
            details = self.tracker['shows'][show]
        except KeyError:
            raise ShowNotTrackedError

        for which in ('next', 'previous'):
            details[which]['episode'] += 1

        # TODO: Validate episodes

    def __iter__(self):
        return iter(self._shows)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.path_to_tracker)


def process_args():
    """Process command line arguments."""
    pass


def main(args):
    """Main entry point for this utility"""
    # test_update_database()
    watchlist = ProcessWatchlist()
    show_database = ShowDatabase()
    tracker = TrackerDatabase()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
