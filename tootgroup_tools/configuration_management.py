## Manages the applications config file storage location, reading
## and writing.

import appdirs
import configparser
import mastodon
import os
import sys


def new_credentials_from_mastodon(config_store, config):
    """Register tootgroup.py at a Mastodon server and get user credentials.
    
    "config_store" dictionary containting config file name and path as
    well as the current group's name

    "config" the configuration as read in from configparser
    
    This will be run if tootgroup.py is started for the first time, if its
    configuration files have been deleted or if some elements of the
    configuration are missing.
    """
    # Register tootgroup.py app at the Mastodon server

    group_name = config_store["group_name"]
    
    try:
        mastodon.Mastodon.create_app(
            "tootgroup.py",
            api_base_url = config[group_name]["mastodon_instance"],
            to_file = config_store["directory"] + config[group_name]["client_id"]
        )
        # Create Mastodon API instance
        masto = mastodon.Mastodon(
            client_id = config_store["directory"] + config[group_name]["client_id"],
            api_base_url = config[group_name]["mastodon_instance"]
        )
    except Exception as e:
        print("")
        print("\n##################################################################")
        print("The Mastodon instance URL is wrong or the server does not respond.")
        print("See the error message for more details:")
        print(e)
        print("")
        print("tootgroup.py will exit now. Run it again to try once more!")
        print("##################################################################\n")
        sys.exit(0)
 
    # Log in once with username and password to get an access token for future logins.
    # Ask until login succeeds or at most 3 times before the skript gives up.
    i = 0
    while i < 3:
        i+=1
        try:
            masto.log_in(
                input("Username (e-Mail) to log into Mastodon Instance: "),
                input("Password: "),
                to_file = config_store["directory"] + config[group_name]["access_token"]
            )
            break
        except Exception:
            print("\nUsername and/or Password did not match!")
            if i <3:
                print("Please enter them again.\n")
            else:
                print("tootgroup.py will exit now. Run it again to try once more!\n")
                sys.exit(0)


def parse_configuration(config_store):
    """Read configuration from file, handle first-run situations and errors.

    "config_store" dictionary containting config file name and path as
    well as the current group's name

    parse_configuration() uses Python's configparser to read and interpret the
    config file. It will detect a missing config file or missing elements and
    then try to solve problems by asking the user for more information. This
    does also take care of a first run situation where nothing is set up yet and
    in that way act as an installer!
    
    parse_configuration should always return a complete and usable configuration"""
    config = configparser.ConfigParser()
    config.read(config_store["directory"] + config_store["filename"])

    group_name = config_store["group_name"]
    get_new_credentials = False

    # Is there already a section for the current tootgroup.py
    # group. If not, create it now.
    if not config.has_section(group_name):
        config[group_name] = {}
        print("Group \"" + group_name + "\" not in configuration. " +
            "- Setting it up now...")
        config_store["write_NEW"] = True
    
    # Do we have a mastodon instance URL? If not, we have to
    # ask for it and register with our group's server first.
    if not config.has_option(group_name, "mastodon_instance"):
        config[group_name]["mastodon_instance"] = ""
        print("We need a Mastodon server to connect to!")
    if config[group_name]["mastodon_instance"] == "":
        config[group_name]["mastodon_instance"] = input("Enter the "
            "URL of the Mastodon instance your group account is "
            "running on: ")
        get_new_credentials = True
        config_store["write_NEW"] = True
    
    # Where can the client ID be found and does the file exist?
    # If not, re-register the client.
    if not config.has_option(group_name, "client_id"):
        config[group_name]["client_id"] = ""
    if config[group_name]["client_id"] == "":
        config[group_name]["client_id"] = group_name + "_clientcred.secret"
        get_new_credentials = True
        config_store["write_NEW"] = True
    if not os.path.isfile(config_store["directory"] + config[group_name]["client_id"]):
        get_new_credentials = True
    
    # Where can the user access token be found and does the file exist?
    # If not, re-register the client to get new user credentials
    if not config.has_option(group_name,  "access_token"):
        config[group_name]["access_token"] = ""
    if config[group_name]["access_token"] == "":
        config[group_name]["access_token"] = group_name + "_usercred.secret"
        get_new_credentials = True
        config_store["write_NEW"] = True
    if not os.path.isfile(config_store["directory"] + config[group_name]["access_token"]):
        get_new_credentials = True
    
    # Should tootgroup.py accept direct messages for reposting?
    if not config.has_option(group_name,  "accept_dms"):
        config[group_name]["accept_dms"] = ""
    if ((config[group_name]["accept_dms"] == "") or
            (config[group_name]["accept_dms"] not in ("yes",  "no"))):
        str = ""
        while True:
            str = input("\nShould tootgroup.py repost direct messages " +
                        "from group members? [yes/no]: ")
            if str.lower() not in ("yes",  "no"):
                print("Please enter 'yes' or 'no'!")
                continue
            else:
                break
        config[group_name]["accept_dms"] = str.lower()
        config_store["write_NEW"] = True

    # How public should the toots from direct messages be?
    while config[group_name].get("dm_visibility") not in {
            'private', 'unlisted', 'public'}:

        config[group_name]["dm_visibility"] = input(
                "\nWhat visibility should the toots created from DMs " +
                "have? Unlisted is recommended for testing, public for " +
                "regular use.\n[private|unlisted|public]: ").lower()
        config_store["write_NEW"] = True
    
    # Should tootgroup.py accept public mentions for retooting?
    if not config.has_option(group_name, "accept_retoots"):
        config[group_name]["accept_retoots"] = ""
    if ((config[group_name]["accept_retoots"] == "") or
            (config[group_name]["accept_retoots"] not in ("yes",  "no"))):
        str = ""
        while True:
            str = input("\nShould tootgroup.py retoot public mentions " +
                        "from group members? [yes/no]: ")
            if str.lower() not in ("yes",  "no"):
                print("Please enter 'yes' or 'no'!")
                continue
            else:
                break
        config[group_name]["accept_retoots"] = str.lower()
        config_store["write_NEW"] = True
    
    # The ID of the last group-toot is needed to check for newly arrived
    # notifications and will be persisted here. It is initially set up with
    # "catch-up" to indicate this situation.
    # Tootgroup.py will then get sane values and continue.
    if ((not config.has_option(group_name, "last_seen_id")) or
            (config[group_name]["last_seen_id"] == "")):
        config[group_name]["last_seen_id"] = "catch-up"
        config_store["write_NEW"] = True
    
    # Some registration info or credentials were missing - we have to register
    # tootgroup.py with our Mastodon server instance. (again?)
    if get_new_credentials:
        print("Some credentials are missing, need to get new ones...")
        new_credentials_from_mastodon(config_store, config)
    
    # Have there been any changes to the configuration?
    # If yes we have to write them to the config file
    if config_store["write_NEW"]:
        write_configuration(config_store, config)

    # Configuration should be complete and working now - return it.
    return(config)


def setup_configuration_store():
    """Search for the configuration file location. Start with the
    skript's home directory and try the OS specific user configuration
    directory next. Local takes precedence but if no configuration
    is found, the new one will be created in the OS specific user
    config path if possible. If that fails, the local directory will
    again be used as a last resort. This is to ensure
    backwards-compatibility and to enable local overrides for
    development/testing.

    Returns a dictinary containing  basic information about how to
    find the configuration. Some dictionary values will be populated
    later (see below for available fields)"""

    config_store = {"filename": "",
                    "directory": "",
                    "group_name": "",
                    "write_NEW" : True }

    # Get name and path of the running application. It is used to
    # determine its configuration storage path
    stack = sys._getframe(1).f_globals  # get caller's globals
    application_namepath = stack["__file__"]
    application_path, application_name = os.path.split(application_namepath)
    application_path = application_path + "/"

    # The config file is named after the application with
    # the extension is changed from ".py" to ".conf"
    # Only the last occurence of ".py" is replaced!
    old_ext = ".py"
    new_ext = ".conf"
    config_filename = new_ext.join(application_name.rsplit(old_ext,1))
    config_store["filename"] = config_filename

    local_path = application_path
    os_user_config_path = appdirs.AppDirs(application_name).user_data_dir + "/"
    config_store["directory"] = local_path 

    # Is there a config file in the tootgroup.py directory?
    if os.path.isfile(local_path + config_filename):
        config_store["write_NEW"] = False
        print("Found local configuration and using it...")

    # Is there a config file in the system's user config directory?
    elif os.path.isfile(os_user_config_path + config_filename):
        config_store["directory"] = os_user_config_path
        config_store["write_NEW"] = False
        # This is the default, do not output anything
    
    # Did not find any config file, default to user config dir!
    else:
        config_store["directory"] = os_user_config_path
        # Create config dir if it does not exist yet
        try:
            os.makedirs(config_store["directory"], exist_ok=True)
            print("No configuration found!")
            print("tootgroup.py will continue to run but first " +
            "ask for all information it requires...\n" +
            "Configuration will then be stored under " +
            config_store["directory"] + "\n")
        except Exception:
            # Cannot create config directory, have to use the
            # tootgroup.py dir instead 
            config_store["directory"] = local_path
            print("No configuration found!")
            print("tootgroup.py will continue to run but first " +
            "ask for all information it requires...\n" +
            "Configuration will then be stored under " +
            config_store["directory"] + "\n")

    return(config_store)


def write_configuration(config_store, config):
    """Write out the configuration into the config file.
    
    "config_store: dictionary containting config file name and path

    "config" configparser object containing the current configuration.
    
    This can be called whenever the configuration needs to be persisted by
    writing it to the disk."""
    print(config_store["directory"])
    try:
        with open(config_store["directory"] + config_store["filename"], "w") as configfile:
            config.write(configfile)

    except Exception as e:
        print("")
        print("\n############################################################")
        print("Cannot write to configuration file:")
        print(e)
        print("Try to fix the problem and run toogroup.py again afterwards.")
        print("############################################################\n")
        sys.exit(0)
