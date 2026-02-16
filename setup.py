import configparser
import os
import sys
import webbrowser

import questionary
from plexapi.myplex import MyPlexAccount, MyPlexPinLogin

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "plex_config.ini")


def prompt(label, default=None):
    if default is not None:
        value = input(f"{label} [{default}]: ").strip()
        return value if value else default
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  This field is required.")


def authenticate():
    print("\nOpening Plex login in your browser...")
    print("(If the browser does not open, copy the URL printed below.)\n")

    pinlogin = MyPlexPinLogin(oauth=True)
    pinlogin.run(timeout=300)

    url = pinlogin.oauthUrl()
    print(f"  {url}\n")
    webbrowser.open(url)

    print("Waiting for you to log in... (5 minute timeout)")
    if not pinlogin.waitForLogin():
        print("\nLogin timed out or failed. Please run setup.py again.")
        sys.exit(1)

    print("Login successful!")
    return pinlogin.token


def pick_server(account):
    servers = [r for r in account.resources() if 'server' in r.provides]

    if not servers:
        print("\nNo Plex servers found on this account. Enter the server name manually.")
        return prompt("Server name")

    print("\nAvailable Plex servers:")
    online = []
    offline = []
    for r in servers:
        if r.presence:
            online.append(r)
        else:
            offline.append(r)

    for i, r in enumerate(online, 1):
        print(f"  {i}. {r.name}  [online]")
    for r in offline:
        print(f"     {r.name}  [offline]")

    while True:
        choice = input(f"\nPick a server (1-{len(online)}) or type a name: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(online):
                return online[idx].name
        elif choice:
            return choice
        print("  Invalid choice, try again.")


def pick_library(plex):
    sections = [s for s in plex.library.sections() if s.type == 'show']

    if not sections:
        print("\nNo TV libraries found on this server. Enter the library name manually.")
        return prompt("Library name")

    print("\nTV libraries on this server:")
    for i, s in enumerate(sections, 1):
        print(f"  {i}. {s.title}")

    while True:
        choice = input(f"\nPick a library (1-{len(sections)}): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sections):
                return sections[idx].title
        print("  Invalid choice, try again.")


def pick_shows(plex, library_name):
    print(f"\nFetching shows from '{library_name}'...")
    all_shows = sorted(plex.library.section(library_name).all(), key=lambda s: s.title)
    titles = [s.title for s in all_shows]

    selected = questionary.checkbox(
        "Select shows to shuffle  (space = toggle, enter = confirm):",
        choices=titles,
    ).ask()

    if selected is None:
        print("Cancelled.")
        sys.exit(0)
    if not selected:
        print("No shows selected. Please select at least one show.")
        return pick_shows(plex, library_name)

    return ", ".join(selected)


def collect_config(plex):
    library_name = pick_library(plex)
    tv_shows = pick_shows(plex, library_name)
    return library_name, tv_shows


def write_config(token, server_name, library_name, tv_shows):
    config = configparser.ConfigParser()
    config["plex_config"] = {
        "token": token,
        "server_name": server_name,
        "library_name": library_name,
        "tv_shows": tv_shows,
    }
    with open(config_path, "w") as f:
        config.write(f)
    print(f"\nConfig written to: {config_path}")


if __name__ == "__main__":
    print("=== Proper Plex Shuffle — Setup ===")
    print("This will open Plex in your browser to log in.")
    print("Your credentials are never seen or stored by this app.\n")

    token = authenticate()
    account = MyPlexAccount(token=token)
    server_name = pick_server(account)
    print(f"\nConnecting to {server_name}...")
    plex = account.resource(server_name).connect()
    library_name, tv_shows = collect_config(plex)
    write_config(token, server_name, library_name, tv_shows)

    print("\nAll done! Next steps:")
    print("  docker compose build")
    print("  docker compose up -d")
    print("\nThe container will refresh your playlists daily at midnight.")
    print("To run immediately: docker exec plex_shuffle /usr/local/bin/python3 /app/refresh_playlists.py")
