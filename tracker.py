#!/usr/env/bin python
"""
Utility to keep track of TV shows
"""
import argparse
import datetime
import json
# import logging
import os
import re
import sys

import requests

from exceptions import (
    DatabaseNotFoundError,
    EpisodeOutOfBoundsError,
    FoundFilmError,
    InvalidOperationError,
    OutOfBoundsError,
    SeasonEpisodeParseError,
    SeasonOutOfBoundsError,
    ShowNotFoundError,
    ShowNotTrackedError,
    # WatchlistNotFoundError,
)
from utils import (
    check_for_databases,
    Deserializer,
    EncodeShow,
    extract_episode_details,
    get_show_database_entry,
    lunderize,
    ProcessWatchlist,
    RegisteredSerializable,
    sanitize_title,
    titleize,
)

# TODO: Add logging
# TODO: Retrieve IGN ratings
# TODO: Retrieve episode synopsis


class Database(RegisteredSerializable):
    """Provide base method for different types of databases"""
    def __init__(
        self,
        database_dir=None,
        _shows=None,
    ):
        if database_dir is None:
            database_dir = os.path.join(os.path.expanduser('~'), '.showtracker')
        self.database_dir = database_dir

        self._shows = {} if _shows is None else _shows

    def create_db_from_watchlist(self, watchlist_path):
        """Create a database from a watchlist"""
        watchlist = ProcessWatchlist(watchlist_path)
        for show in watchlist:
            self.add_show(show)

    def write_db(self, indent=None):
        """Write database to disk"""
        try:
            os.mkdir(self.database_dir)
        except OSError:
            # logger.debug('os.mkdir failed: directory=%r already exists',
            #     self.database_dir)
            pass  # TODO: Remove pass, and enable logging

        with open(self.path_to_db, 'w', encoding='utf-8') as f:
            json.dump(self, f, cls=EncodeShow, indent=indent, sort_keys=True)


class ShowDatabase(Database):
    def __init__(
        self,
        database_dir=None,
        path_to_db=None,
        # showdb_name=None,
        _shows=None,
    ):
        super().__init__(database_dir, _shows)

        # self.showdb_name = '.showdb.json' if showdb_name is None else showdb_name
        showdb_name = '.showdb.json'
        if path_to_db is None:
            self.path_to_db = os.path.join(self.database_dir, showdb_name)
        else:
            self.path_to_db = path_to_db

        # if not os.path.exists(self.path_to_showdb):
        #     self.create_database()

    def add_show(self, show_details):
        """Add a show to the database.

        Args:
            show_details: namedtuple with the following fields:
                show_title
                next_episode
                notes
        Example show_details:
                'Game of Thrones'
                'S01E01'
                'Pilot episode'
        """
        title = show_details.show_title
        show = Show(title)
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

    def __contains__(self, key):
        return key in self._shows

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.path_to_db)



class TrackerDatabase(Database):
    """Provided methods to read current tracker information.

    Available methods:
        next_episode:
    """
    def __init__(
        self,
        database_dir=None,
        path_to_db=None,
        # tracker_name=None,
        # showdb_name=None,
        _shows=None,
    ):
        super().__init__(database_dir, _shows)

        # TODO: Do tracker_name and showdb_name need to be instance attributes?
        # self.tracker_name = '.tracker.json' if tracker_name is None else tracker_name
        tracker_name = '.tracker.json'
        if path_to_db is None:
            self.path_to_db = os.path.join(self.database_dir, tracker_name)
        else:
            self.path_to_db = path_to_db

        # self.path_to_tracker = os.path.join(self.database_dir, self.tracker_name)

        # self.showdb_name = '.showdb.json' if showdb_name is None else showdb_name
        # self.path_to_showdb = os.path.join(self.database_dir, self.showdb_name)

        # if not os.path.exists(self.path_to_tracker):
        #     self.create_database()
        #     show_db = load_database(self.path_to_showdb)
        #     self._add_next_prev_episode(show_db)

    def add_show(self, show_details):
        show = TrackedShow(
            title=show_details.show_title,
            _next_episode=show_details.next_episode,
            notes=show_details.notes,
        )
        self._shows[show.ltitle] = show

    def create_tracker_from_watchlist(self, watchlist_path, showdb=None):
        """Create a tracker database from a watchlist"""
        if showdb is None:
            # Attempt to load the ShowDatabase from the common database
            # directory
            try:
                showdb = load_database(
                    os.path.join(os.path.dirname(self.path_to_db), '.showdb.json')
                )
            except FileNotFoundError:
                # TODO: Log this
                pass

        self.create_db_from_watchlist(watchlist_path)
        self._add_next_prev_episode(showdb)

    def _add_next_prev_episode(self, showdb):
        """Add the next and previous episodes for the tracked show"""
        # TODO: Do I really have to call .values()
        for show in self._shows.values():
            try:
                show._set_next_prev(showdb)
            except OutOfBoundsError:
                pass  # TODO: Add proper handling

    def _short_codes(self):
        for s in self._shows:
            yield self._shows[s].short_code

    def __iter__(self):
        return iter(self._shows)

    def __contains__(self, key):
        full_title = key in self._shows
        short_code = key in self._short_codes()
        return full_title or short_code

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.path_to_db)


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

    def __repr__(self):
        return 'ShowDetails(title={!r})'.format(self.title)


class TrackedShow(ShowDetails):
    """Keep track of next and previous episodes of a tracked show.

    Available methods:
        inc_episode
    """
    def __init__(
        self,
        title=None,
        ltitle=None,
        request_title=None,
        _next_episode='s01e01',
        notes=None,
        short_code=None,
        _next=None,
        _prev=None,
    ):
        super().__init__(title, short_code)
        self._next = _next
        self.notes = notes
        self._prev = _prev
        self._next_episode = _next_episode

    def _get_season_episode_from_str(self):
        """Extract a season and episode from a string."""
        pattern = r'[sS](\d{1,2})[eE](\d{1,2})'
        m = re.search(pattern, self._next_episode)

        if not m:
            raise SeasonEpisodeParseError

        season = int(m.group(1))
        episode = int(m.group(2))
        return season, episode

    def _set_next_prev(self, show_database):
        """Set up the next and previous episodes of a TrackedShow"""

        show_db = get_show_database_entry(show_database, title=self.ltitle)

        season, episode = self._get_season_episode_from_str()
        # Account for zero-indexing.
        # The first season or first episode will should be referenced as
        # episode zero.
        season, episode = season-1, episode-1

        self._validate_season_episode(show_db, season, episode)

        self._next = show_db._seasons[season]._episodes[episode]

        if season == 0 and episode == 0:
            return
        elif episode == 0:
            season -= 1
            episode = show_db._seasons[season].episodes_this_season - 1
        else:
            episode -= 1

        self._prev = show_db._seasons[season]._episodes[episode]

    def inc_dec_episode(self, show_database, inc=False, dec=False):
        """x"""
        if inc and dec:
            raise InvalidOperationError

        if not (inc and dec):
            return

        # May raise a ShowNotFoundError
        show_db = get_show_database_entry(show_database, title=self.ltitle)

        season, episode = self._adjust_season_episode(inc, dec)

    def _adjust_season_episode(self, inc, dec):
        """Return a zero-index adjusted season and episode"""
        if inc:
            return self._next.season-1, self._next.episode-1
        elif dec:
            try:
                season, episode = self._prev.season-1, self._prev.episode-1
            except AttributeError:
                # self.prev is None, meaning we are dealing with the first
                # episode of a show (S01E01).
                season, episode = 0, 0

            return season, episode

    def _validate_season_episode(self, show_db, season, episode):
        """Check that the season and episode passed are valid."""

        try:
            season = show_db._seasons[season]
        except IndexError:
            raise SeasonOutOfBoundsError

        try:
            episode = season._episodes[episode]
        except IndexError:
            raise EpisodeOutOfBoundsError

    def inc_episode(self, show_database, by=1):
        """Advance the next episode for a tracked show.

        Args:
            show_database: a ShowDatabase
            by: How many episodes to increment from the current
                episode. Default is to advance by one episode.

        Raises:
            ShowNotFoundError
            SeasonOutOfBoundsError
            EpisodeOutOfBoundsError
        """
        # May raise a ShowNotFoundError
        show_db = get_show_database_entry(show_database, title=self.ltitle)

        season, episode = self._next.season-1, self._next.episode-1

        for inc in range(by):
            # Check if the current ('old') next_episode is the season finale
            # If so, the 'new' next_episode will be the next season premiere.
            if self._next.episode == show_db._seasons[season].episodes_this_season:
                season += 1
                episode = 0
            else:
                episode += 1

            self._validate_season_episode(show_db, season, episode)

            self._prev = self._next
            self._next = show_db._seasons[season]._episodes[episode]

    def dec_episode(self, show_database, by=1):
        """Decrement the next episode for a tracked show.

        Args:
            show_database: a ShowDatabase
            by: How many episodes to decrement from the current
                episode. Default is to decrement by one episode.

        Raises:
            ShowNotFoundError
            SeasonOutOfBoundsError
            EpisodeOutOfBoundsError
        """
        show_db = get_show_database_entry(show_database, title=self.ltitle)

        try:
            season, episode = self._prev.season-1, self._prev.episode-1
        except AttributeError:
            # self.prev is None
            season, episode = 0, 0

        for dec in range(by):
            if season == 0 and episode == 0:
                self._next = show_db._seasons[season]._episodes[episode]
                break  # TODO: Perhaps raise something
            # Decrement over a season boundary, for season > 0.
            # Set the episode to the finale of the previous season
            elif episode == 0:
                season -= 1
                episode = show_db._seasons[season].episodes_this_season-1
            else:
                episode -= 1

            self._validate_season_episode(show_db, season, episode)

            self._next = self._prev
            self._prev = show_db._seasons[season]._episodes[episode]

    def __repr__(self):
        return ('TrackedShow(title={self.title!r}, _next_episode={self._next_episode!r}, '
            'notes={self.notes!r}, short_code={self.short_code!r})'.format(self=self))


class Show(ShowDetails):
    """Represent various details of a show.

    Available attributes:
        next
    """
    def __init__(
        self,
        title=None,
        ltitle=None,
        request_title=None,
        short_code=None,
        _seasons=None
    ):
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


def load_database(path_to_database):
    """Return an existing database"""
    try:
        with open(path_to_database, 'r') as db:
            deserialized_data = json.load(db)
    except FileNotFoundError:
        raise DatabaseNotFoundError
    else:
        deserializer = Deserializer(deserialized_data)
        database = deserializer.deserialize()

    return database


def load_all_dbs(database_dir):
    """Load and return a ShowDB and TrackerDB.

    Returns:
        showdb: ShowDatabse instance
        tracker: TrackerDatabase instance

    """
    showdb = load_database(os.path.join(database_dir, '.showdb.json'))
    tracker = load_database(os.path.join(database_dir, '.tracker.json'))
    return showdb, tracker


def update_database():
    """Update an existing ShowDatabase.
    """
    # TODO: Locate the database

    # TODO: Rename the database

    # TODO: Get list of existing shows in database

    # TODO: Read watchlist

    # TODO: Combine two lists of shows

    # TODO: Create database

    # TODO: Test database is valid

    # TODO: Write database, and exit


# def update(self, from_file=True):
#     if from_file:
#         self.next['season'], self.next['episode'] = show_update()


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
    tracker = TrackerDatabase()
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


def process_args():
    """Process command line arguments."""
    parser = argparse.ArgumentParser(
        description='Utility to facilitate the tracking of TV shows',
        prefix_chars='-+',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        # add_help=False,
    )

    show_kwargs = {
        'help': 'title of show',
    }

    parser.add_argument(
        '-l',
        '--list',
        help='list tracked shows',
        action='store_true',
        # default=5,
        # metavar='N',
    )

    parser.add_argument(
        '-w',
        '--watchlist',
        help='read a watchlist',
        nargs='?',
        const='watchlist.txt',
    )

    subparsers = parser.add_subparsers(help='sub-commands', dest='sub_command')

    parser_add = subparsers.add_parser(
        'add',
        help='add info to an existing show',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_dec = subparsers.add_parser(
        'dec',
        help='decrement the next episode of a show',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_inc = subparsers.add_parser(
        'inc',
        help='increment the next episode of a show',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_next = subparsers.add_parser(
        'next',
        help='print details for the next episode',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser_add.add_argument('show', **show_kwargs)
    parser_add.set_defaults(func=command_add)

    parser_dec.add_argument('show', **show_kwargs)
    parser_dec.set_defaults(func=command_dec)

    parser_inc.add_argument('show', **show_kwargs)
    parser_inc.set_defaults(func=command_inc)

    parser_next.add_argument('show', **show_kwargs)
    parser_next.set_defaults(func=command_next)

    parser_add.add_argument(
        # '-n',
        '--note',
        help='add a note to the show',
        # nargs='*',
    )
    parser_add.add_argument(
        '-c',
        '--short-code',
        help='add a short_code to the show',
        # metavar='SHORT_CODE',
    )

    parser_dec.add_argument(
        '--by',
        help='decrement the currently tracked episode by B',
        default=1,
        metavar='B',
    )

    parser_inc.add_argument(
        '--by',
        help='increment the currently tracked episode by B',
        default=1,
        metavar='B',
    )

    return parser  #.parse_args()


def command_watchlist():
    showdb = ShowDatabase()


def command_add(args):
    if args.note:
        print('add note="{}" to show="{}"'.format(args.note, args.show))
    if args.short_code:
        print('add short_code="{}" to show="{}"'.format(args.short_code, args.show))

    if not args.note and not args.short_code:
        print('Add show={}'.format(args.show))


def command_dec(args):
    print('Dec. {} by {} episodes'.format(args.show, args.by))


def command_inc(args):
    print('Inc. {} by {} episodes'.format(args.show, args.by))


def command_next(args):
    # >> Next episodes for 2 shows:
    # Show             | Next episode
    # ------------------------------------
    # Game of Thrones  | S06 E04
    # Supernatural     | S11 E21
    print('Next episode for \'{}\': S{} E{})')
    return '< {self.title} (S{self.season:02d}E{self.episode:02d}) >'.format(
        self=self
    )


def main(args):
    """Main entry point for this utility"""
    parser = process_args()
    args = parser.parse_args()

    # TODO: Remove this
    print(args)

    db_check = check_for_databases()
    # TODO: Remove this
    print(db_check)

    if db_check.showdb_exists and db_check.tracker_exists:
        pass
    elif db_check.showdb_exists and not db_check.tracker_exists:
        # TODO: Add error handling. Exit for now.
        print('Tracker database not found')
        sys.exit()
    elif not db_check.showdb_exists and db_check.tracker_exists:
        # TODO: Add error handling. Exit for now.
        print('Show Database not found')
        sys.exit()
    else:
        # Neither database present
        # Now need to check that either --list, or --watchlist was passed
        # If neither, then exit.
        if not (args.list or args.watchlist or args.sub_command):
            print()
            parser.print_help()
            # print('No databases found. No vaild option passed. Exiting.')
            sys.exit()


    # Order of precedence:
    # 1. List
    # 2. Watchlist
    # 3. Subcommands
    if args.list:
        # list handling
        pass
    elif args.watchlist:
        # watchlist handling
        pass
    else:
        args.func(args)

    # if not os.path.exists(showdb)
    # list_episodes()
    # test_update_database()
    # watchlist = ProcessWatchlist()
    # show_database = ShowDatabase()
    # tracker = TrackerDatabase()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
