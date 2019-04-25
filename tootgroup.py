#!/usr/bin/env python3

## tootgroup.py
## Version 1.0
##
##
## Andreas Schreiner
## @andis@chaos.social
## andreas.schreiner@sonnenmulde.at
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## any later version.
##
## See attached LICENSE file.
##

import argparse
import configparser
import html
import os
import re
import requests
import sys
import tempfile

from appdirs import AppDirs
from mastodon import Mastodon



# Execution starts here.
def main():

    # Read commandline arguments and flags from input
    my_commandline_arguments = parse_arguments()

    # Get the configuration storage loocation
    my_config_dir, my_config_file = setup_configuration_path("tootgroup.py",
        "tootgroup.conf") 
    write_new_config = False

    # Get the Mastodon account handle the script is running for.
    my_group_name = my_commandline_arguments["group_name"]

    # Get and validate configuration from the config file.
    my_config = parse_configuration(my_config_dir, my_config_file, my_group_name)

    # If the "catch-up" commandline argument has been given, reset the last seen
    # ID so that tootgroup.py only updates its according config value without
    # retooting anything.
    if my_commandline_arguments["catch_up"]:
        my_config[my_group_name]["last_seen_id"] = "catch-up" 
    
    # Create Mastodon API instance.
    mastodon = Mastodon(
        client_id = my_config_dir + my_config[my_group_name]["client_id"],
        access_token = my_config_dir + my_config[my_group_name]["access_token"],
        api_base_url = my_config[my_group_name]["mastodon_instance"]
    )
    
    try:
        # Get the group account information.
        # This connects to the Mastodon server for the first time at
        # every tootgroup.py's run.
        my_account = {
            "username": mastodon.account_verify_credentials().username, 
            "id": mastodon.account_verify_credentials().id, 
            "group_member_ids": []
        }
    except Exception as e:
        print("")
        print("\n########################################################")
        print("tootgroup.py could not connect to the Mastodon server.")
        print("If you know that it is running, there might be a")
        print("problem with our local configuration. Check the error")
        print("message for more details:")
        print(e)
        print("\nYou can always try to delete tootgroup.py's config file")
        print("and re-run the script for a new setup.")
        print("########################################################\n")
        sys.exit(0)

    # Get group member IDs that could net be fetched directly while
    # connecting to the Mastodon server.
    for member in mastodon.account_following(my_account["id"]):
        my_account["group_member_ids"].append(member.id)
    
    # Do we accept direct messages, public retoots, both or none? This
    # can be set in the configuration.
    accept_DMs = my_config[my_group_name].getboolean("accept_DMs")
    accept_retoots = my_config[my_group_name].getboolean("accept_retoots")
    
    # Get all new notifications up to a maximum number set here.
    # Defaults to 100 and has to be changed in the code if really desired.
    # Use the ID of the last seen notification for deciding what is new.
    notification_count = 0
    max_notifications = 100
    max_notification_id = None
    latest_notification_id = 0
    my_notifications = []
    get_more_notifications = True
    
    # Get notifications. Stop if either the last known notification ID or
    # the maximum number is reached. Chunk size is limited to 40 by Mastodon
    # but could be reduced further by any specific server instance. 
    while get_more_notifications:
        get_notifications = mastodon.notifications(max_id = max_notification_id)
        
        # Remember the ID of the latest notification on first iteration
        if notification_count == 0:
            if len(get_notifications) > 0:
                latest_notification_id = get_notifications[0].id
            else: # If there have not been any notifications yet, set value to "0"
                latest_notification_id = 0
                print("Nothing to do yet! Start interacting with your group account first.")
                get_more_notifications = False
        else: # leave the while loop if there are no more notifications fetched
            if len(get_notifications) == 0:
                get_more_notifications = False

        # Initialize "last_seen_id" on first run. Notifications are ignored up
        # to this point, but newer ones will be considered subsequently.
        if my_config[my_group_name]["last_seen_id"] == "catch-up":
            my_config[my_group_name]["last_seen_id"] = str(latest_notification_id)
            write_new_config = True
            print("Caught up to current timeline. Run again to start group-tooting.")
        
        for notification in get_notifications:
            max_notification_id = notification.id
            
            if (notification.id > int(my_config[my_group_name]["last_seen_id"]) and
                    notification_count < max_notifications):
                my_notifications.append(notification)
            else:
                get_more_notifications = False
                break
            
            notification_count += 1
    
    # If there have been new notifications since the last run, update "last_seen_id"
    # and write config file to persist the new value.
    if latest_notification_id > int(my_config[my_group_name]["last_seen_id"]):
        my_config[my_group_name]["last_seen_id"] = str(latest_notification_id)
        write_new_config = True
    
    # Reverse list of notifications so that the oldest are processed first
    my_notifications = my_notifications[::-1]

    # run through the notifications and look for retoot candidates
    for notification in my_notifications:
        
        # Only from group members
        if notification.account.id in my_account["group_member_ids"]:
        
            # Is retooting of public mentions configured?
            if accept_retoots:
                if notification.type == "mention" and notification.status.visibility == "public":
                    # Only if the mention was preceeded by an "!". 
                    # To check this, html tags have to be removed first.
                    repost_trigger = "!@" + my_account["username"]
                    status = re.sub("<.*?>", "", notification.status.content)
                    if repost_trigger in status:
                        if not my_commandline_arguments["dry_run"]:
                            mastodon.status_reblog(notification.status.id)
                            print("Retooted from notification ID: " + str(notification.id))
                        else:
                            print("DRY RUN - would have retooted from notification ID: "
                                + str(notification.id))
    
            # Is reposting of direct messages configured? - if yes then:
            # Look for direct messages
            if accept_DMs:
                if notification.type == "mention" and notification.status.visibility == "direct":
                    
                    # Remove HTML tags from the status content but keep linebreaks
                    new_status = re.sub("<br />", "\n", notification.status.content)
                    new_status = re.sub("</p><p>", "\n\n", new_status)
                    new_status = re.sub("<.*?>", "", new_status)
                    # Remove the @username from the text
                    rm_username = "@" + my_account["username"]
                    new_status = re.sub(rm_username, "", new_status)
                    # "un-escape" HTML special characters
                    new_status = html.unescape(new_status)
                    if not my_commandline_arguments["dry_run"]:
                        # Repost as a new status
                        mastodon.status_post(
                            new_status,
                            media_ids = media_toot_again(notification.status.media_attachments,
                                mastodon),
                            sensitive = notification.status.sensitive,
                            visibility = "public",
                            spoiler_text = notification.status.spoiler_text
                        )
                        print("Newly posted from notification ID: " + str(notification.id))
                    else:
                        print("DRY RUN - would have newly posted from notification ID: "
                            + str(notification.id))
    
    # There have been changes requiring to persist the new configuration
    # but not in a dry-run condition
    if write_new_config and not my_commandline_arguments["dry_run"]:
        write_configuration(my_config_dir, my_config_file, my_config)
    
    print("Successful tootgroup.py run for " + "@" + my_account["username"] +
        " at " + my_config[my_group_name]["mastodon_instance"])



def media_toot_again(orig_media_dict, mastodon_instance):
    """Re-upload media files to Mastodon for use in another toot.
    
    "orig_media_dict" - extracted media files from the original toot

    "mastodon_instance" - needed to re-upload the media files and create
    a new media_dict.
    
    Mastodon does not allow the re-use of already uploaded media files (images,
    videos) in a new toot. This function downloads all media files from a toot
    and re-uploads them. It then returns a dict formatted in a proper way to
    be used by the Mastodon.status_post() function."""
    new_media_dict = []
    for media in orig_media_dict:
        media_data = requests.get(media.url).content
        filename = os.path.basename(media.url)
        # basename still includes a "?" followed by a number after the file's name.
        # Remove them both.
        filename = filename.split("?")[0]
        # separate filename and extension
        filename, file_ext = os.path.splitext(filename)
        f_temp = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False, mode="w+b")
        try:  
            f_temp.write(media_data)
            f_temp.close() # close to flush data
            # This re-uploads the current media file to Mastodon!
            new_media_dict.append(mastodon_instance.media_post(
                f_temp.name, description=media.description))
        except Exception as e:
            print("")
            print("\n##################################################################")
            print("Cannot write media to temporary file:")
            print(e)
            print("")
            print("tootgroup.py will continue but media files might not get reposted!")
            print("##################################################################\n")
        finally:  
            f_temp.close() # close again for good measure
            try:
                os.unlink(f_temp.name) # delete temporary file
            except Exception:
                pass # cannot delete, probably non-existant anyway! 
    return(new_media_dict)



def new_credentials_from_mastodon(group_name, config_dir, config):
    """Register tootgroup.py at a Mastodon server and get user credentials.
    
    "group_name" points to the current groups settings in the config file

    "config_dir" directory where the config and credentials are stored

    "config" the configuration as read in from configparser
    
    This will be run if tootgroup.py is started for the first time, if its
    configuration files have been deleted or if some elements of the
    configuration are missing.
    """
    # Register tootgroup.py app at the Mastodon server
    try:
        Mastodon.create_app(
            "tootgroup.py",
            api_base_url = config[group_name]["mastodon_instance"],
            to_file = config_dir + config[group_name]["client_id"]
        )
        # Create Mastodon API instance
        mastodon = Mastodon(
            client_id = config_dir + config[group_name]["client_id"],
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
            mastodon.log_in(
                input("Username (e-Mail) to log into Mastodon Instance: "),
                input("Password: "),
                to_file = config_dir + config[group_name]["access_token"]
            )
            break
        except Exception:
            print("\nUsername and/or Password did not match!")
            if i <3:
                print("Please enter them again.\n")
            else:
                print("tootgroup.py will exit now. Run it again to try once more!\n")
                sys.exit(0)



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

    -k, --ketchup: Same as -c or --catch-up, for the sake of lol."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--catch-up", action="store_true",
        help="Catch up to the current state of the timeline without tooting " +
        "anything. This is useful if the script has not been running for a " +
        "while and would otherwise (re)post lots of old group-toots.")
    parser.add_argument("-d", "--dry-run", action="store_true",
        help="Parse new messages but do not upload or toot anything. " +
        "Shows the ID of notifications it would have processed instead.")
    parser.add_argument("-g", "--group",  default="default", 
        help="Input a handle for the Mastodon account. tootgroup.py stores all " +
        "information connected to a specific group account under this name. " +
        "By choosing different handles it is possible to manage multiple " +
        "Mastodon groups from the same skript. This can be chosen freely but " +
        " it is wise to use a name that is related to the Mastodon account " +
        " it will be used with. If no handle is given, " +
        "\"%(default)s\" is always used instead.")
    parser.add_argument("-k", "--ketchup", action="store_true",
        help="Same as -c or --catch-up for the sake of lol!")
    args = parser.parse_args()    
    arguments = {}
    arguments["group_name"] = args.group
    arguments["catch_up"] = False
    arguments["dry_run"] = False
    if args.catch_up or args.ketchup:
        arguments["catch_up"] = True
    if args.dry_run:
        arguments["dry_run"] = True

    return arguments



def parse_configuration(config_dir, config_file,  group_name):
    """Read configuration from file, handle first-run situations and errors.
    
    "config_dir" the OS specific path to the configuration directory 

    "config_file" the name of the configuration file 

    "group_name" determines the section to be read by configparser
    
    parse_configuration() uses Python's configparser to read and interpret the
    config file. It will detect a missing config file or missing elements and
    then try to solve problems by asking the user for more information. This
    does also take care of a first run situation where nothing is set up yet and
    in that way act as an installer!
    
    parse_configuration should always return a complete and usable configuration"""
    config = configparser.ConfigParser()
    config.read(config_dir + config_file)
    get_new_credentials = False
    write_new_config = False
    
    # Is there already a section for the current tootgroup.py
    # group. If not, create it now.
    if not config.has_section(group_name):
        config[group_name] = {}
        print("Group \"" + group_name + "\" not in configuration. " +
            "- Setting it up now...")
        write_new_config = True
    
    # Do we have a mastodon instance URL? If not, we have to
    # ask for it and register with our group's server first.
    if not config.has_option(group_name,  "mastodon_instance"):
        config[group_name]["mastodon_instance"] = ""
        print("We need a Mastodon server to connect to!")
    if config[group_name]["mastodon_instance"] == "":
        config[group_name]["mastodon_instance"] = input("Enter the "
            "URL of the Mastodon instance your group account is "
            "running on: ")
        get_new_credentials = True
        write_new_config = True
    
    # Where can the client ID be found and does the file exist?
    # If not, re-register the client.
    if not config.has_option(group_name,  "client_id"):
        config[group_name]["client_id"] = ""
    if config[group_name]["client_id"] == "":
        config[group_name]["client_id"] = group_name + "_clientcred.secret"
        get_new_credentials = True
        write_new_config = True
    if not os.path.isfile(config_dir + config[group_name]["client_id"]):
        get_new_credentials = True
    
    # Where can the user access token be found and does the file exist?
    # If not, re-register the client to get new user credentials
    if not config.has_option(group_name,  "access_token"):
        config[group_name]["access_token"] = ""
    if config[group_name]["access_token"] == "":
        config[group_name]["access_token"] = group_name + "_usercred.secret"
        get_new_credentials = True
        write_new_config = True
    if not os.path.isfile(config_dir + config[group_name]["access_token"]):
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
        write_new_config = True
    
    # Should tootgroup.py accept public mentions for retooting?
    if not config.has_option(group_name,  "accept_retoots"):
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
        write_new_config = True
    
    # The ID of the last group-toot is needed to check for newly arrived
    # notifications and will be persisted here. It is initially set up with
    # "catch-up" to indicate this situation.
    # Tootgroup.py will then get sane values and continue.
    if ((not config.has_option(group_name,  "last_seen_id")) or
            (config[group_name]["last_seen_id"] == "")):
        config[group_name]["last_seen_id"] = "catch-up"
        write_new_config = True    
    
    # Some registration info or credentials were missing - we have to register
    # tootgroup.py with our Mastodon server instance. (again?)
    if get_new_credentials:
        print("Some credentials are missing, need to get new ones...")
        new_credentials_from_mastodon(group_name, config_dir, config)
    
    # Have there been any changes to the configuration?
    # If yes we have to write them to the config file
    if write_new_config:
        write_configuration(config_dir, config_file, config)
    
    # Configuration should be complete and working now - return it.
    return(config)


def setup_configuration_path(application_name, config_filename):
    """Search for the configuration file location. Start with the
    skript's home directory and try the OS specific user configuration
    directory next. Local takes precedence but if no configuration
    is found, the new one will be created in the OS specific user
    config path if possible. If that fails, the local directory will
    again be used as a last resort. This is to ensure
    backwards-compatibility and to enable local overrides for
    development/testing.
    
    "application_name" used to determine the operating system
    specific config storage path.

    "config_filename" name of the configuration file

    Returns a tuple containing the path to the configuration dir
    and the name of the config file"""
    local_path = os.path.dirname(os.path.realpath(__file__)) + "/"
    os_user_config_path = AppDirs(application_name).user_data_dir + "/"
    config_dir = local_path

    # Is there a config file in the tootgroup.py directory?
    if os.path.isfile(local_path + config_filename):
        print("Found local configuration and using it...")

    # Is there a config file in the system's user config directory?
    elif os.path.isfile(os_user_config_path + config_filename):
        config_dir = os_user_config_path
        # This is the default, do not output anything
    
    # Did not find any config file, default to user config dir!
    else:
        config_dir = os_user_config_path
        # Create config dir if it does not exist yet
        try:
            os.makedirs(config_dir, exist_ok=True)
            print("No configuration found!")
            print("tootgroup.py will continue to run but first " +
            "ask for all information it requires...\n" +
            "Configuration will then be stored under " +
            config_dir + "\n")
        except Exception:
            # Cannot create config directory, have to use the
            # tootgroup.py dir instead 
            config_dir = local_path
            print("No configuration found!")
            print("tootgroup.py will continue to run but first " +
            "ask for all information it requires...\n" +
            "Configuration will then be stored under " +
            config_dir + "\n")

    return(config_dir, config_filename)



def write_configuration(config_dir, config_file,  config):
    """Write out the configuration into the config file.
    
    "config_dir" the path to the configuration directory 
    
    "config_file" the name of the configuration file 

    "config" configparser object containing the current configuration.
    
    This can be called whenever the configuration needs to be persisted by
    writing it to the disk."""
    try:
        with open(config_dir + config_file, "w") as configfile:
            config.write(configfile)
    except Exception as e:
        print("")
        print("\n############################################################")
        print("Cannot write to configuration file:")
        print(e)
        print("Try to fix the problem and run toogroup.py again afterwards.")
        print("############################################################\n")
        sys.exit(0)
            


# Start executing main() function if the script is called from a command line
if __name__=="__main__":
    main()
