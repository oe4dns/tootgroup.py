"""Uses the argparse module to parse arguments/flags given on
the commandline and returns them as a Dictionary."""

import argparse


def parse_arguments():
    """Read arguments from the command line.

    parse_arguments() uses Python's agparser to read arguments from the command
    line. It also sets defaults and provides help and hints abouth which
    arguments are available

    Availble arguments:
    -h, --help: Automatically generated, prints options for help

    -c, --catch-up: Catch up to the current state of the timeline without
    tooting anything. This is useful if the script has not been running for
    a while and would otherwise (re)post lots of old group-toots.

    -d, --dry-run: Parse new messages but do not upload or toot anything.
    Shows the ID of notifications it would have processed instead.

    -g, --group: group handle the script is currently running for. Needed
    by configparser to find its configuration and can be chosen freely.

    -k, --ketchup: Same as -c or --catch-up, for the sake of lol.

    --version: Show tootgroup.py version and exit"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--catch-up",
        action="store_true",
        help="Catch up to the current state of the timeline without tooting "
        + "anything. This is useful if the script has not been running for a "
        + "while and would otherwise (re)post lots of old group-toots.",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Parse new messages but do not upload or toot anything. "
        + "Shows the ID of notifications it would have processed instead.",
    )
    parser.add_argument(
        "-g",
        "--group",
        default="default",
        help="Input a handle for the Fediverse account. tootgroup.py stores all "
        + "information connected to a specific group account under this name. "
        + "By choosing different handles it is possible to manage multiple "
        + "groups from the same skript. The handle can be chosen freely but "
        + " it is wise to use a name that is related to the Fediverse account "
        + " it will be used with. If no handle is given, "
        + '"%(default)s" is always used instead.',
    )
    parser.add_argument(
        "-k",
        "--ketchup",
        action="store_true",
        help="Same as -c or --catch-up for the sake of lol!",
    )
    parser.add_argument(
        "--version", action="store_true", help="Show tootgroup.py version and exit."
    )
    args = parser.parse_args()
    arguments = {}
    arguments["group_name"] = args.group
    arguments["catch_up"] = False
    arguments["dry_run"] = False
    arguments["show_version"] = False
    if args.catch_up or args.ketchup:
        arguments["catch_up"] = True
    if args.dry_run:
        arguments["dry_run"] = True
    if args.version:
        arguments["show_version"] = True

    return arguments
