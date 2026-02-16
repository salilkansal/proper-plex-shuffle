import plexapi.exceptions
from plexapi.myplex import MyPlexAccount
from datetime import date
import logging
import configparser
import random
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "plex_config.ini")

plex_config = configparser.ConfigParser()
plex_config.read(config_path)

TODAY = date.today()

logging.basicConfig(level=logging.INFO)


def save_token_to_config(token):
    """Write the refreshed Plex auth token back to the config file so it
    persists across container restarts via the mounted volume."""
    plex_config.set('plex_config', 'token', token)
    with open(config_path, 'w') as f:
        plex_config.write(f)
    logging.info('Refreshed token saved to config.')


def connect_to_plex(token, server_name):
    """Authenticate against plex.tv using a token, save the refreshed
    authenticationToken back to the config file, then connect to the
    Plex Media Server."""

    account = MyPlexAccount(token=token)
    refreshed_token = account.authenticationToken
    save_token_to_config(refreshed_token)
    plex = account.resource(server_name).connect()

    return plex


def build_tiered_shuffle_playlist(plex, library_name, show_name):
    """Return all episodes grouped into staleness tiers, shuffled within each tier.
    Tier 1 (first): Never watched
    Tier 2: Not watched in 90+ days
    Tier 3: Not watched in 30-90 days
    Tier 4 (last): Watched in last 30 days
    """
    logging.info(f'  Library: {library_name!r}  Show: {show_name!r}')
    plex_current_show = plex.library.section(library_name).get(show_name)
    logging.info(f'  Found show: {plex_current_show.title!r}')

    tier1, tier2, tier3, tier4 = [], [], [], []

    for episode in plex_current_show.episodes():
        if not episode.lastViewedAt:
            tier1.append(episode)
        else:
            days_ago = (TODAY - episode.lastViewedAt.date()).days
            if days_ago >= 90:
                tier2.append(episode)
            elif days_ago >= 30:
                tier3.append(episode)
            else:
                tier4.append(episode)

    logging.info(
        f'  Tiers — never: {len(tier1)}, 90+d: {len(tier2)}, '
        f'30-90d: {len(tier3)}, <30d: {len(tier4)}, total: {len(tier1)+len(tier2)+len(tier3)+len(tier4)}'
    )

    for tier in (tier1, tier2, tier3, tier4):
        random.shuffle(tier)

    return tier1 + tier2 + tier3 + tier4


def delete_existing_playlist(plex, playlist_name):
    """If playlist already exists, delete it."""

    existing_playlists = [playlist.title for playlist in plex.playlists()]
    logging.info(f'Found existing playlists: {existing_playlists}')
    if playlist_name in existing_playlists:
        logging.info(f'Deleting existing playlist: {playlist_name}')
        try:
            plex.playlist(playlist_name).delete()
        except plexapi.exceptions.BadRequest:
#             this is ok and a bug in plex api and causing 204 but no real error found
            logging.info(f'Ate 204 error but was able to delete the playlist')

def create_new_playlist(plex, playlist_name, old_episodes_playlist):
    """Create a new playlist and add all the old episodes to it"""

    plex.createPlaylist(playlist_name, items=old_episodes_playlist)


if __name__ == '__main__':
    tv_shows = plex_config.get('plex_config', 'tv_shows').split(',')

    plex = connect_to_plex(
        token=plex_config.get('plex_config', 'token'),
        server_name=plex_config.get('plex_config', 'server_name')
    )

    for show in tv_shows:
        show = show.strip()
        logging.info(f'Updating playlist for show: {show}...')
        old_episodes_playlist = build_tiered_shuffle_playlist(
            plex,
            library_name=plex_config.get('plex_config', 'library_name'),
            show_name=show
            )
        if not old_episodes_playlist:
            logging.warning(f'No episodes found for {show} — skipping.')
            continue
        delete_existing_playlist(plex, show)
        create_new_playlist(plex, show, old_episodes_playlist)
