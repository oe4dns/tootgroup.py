#!/usr/bin/env python3
## tootgroup.py
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

import tootgroup_tools
TOOTGROUP_VERSION = tootgroup_tools.version.CURRENT

import html
import mastodon
import os
import re
import requests
import sys
import tempfile


# Execution starts here.
def main():

    # Read commandline arguments and flags from input
    commandline_arguments = tootgroup_tools.commandline_arguments.parse_arguments()

    # if the "--version" argument has been given, show version and exit.
    if commandline_arguments["show_version"]:
        tootgroup_tools.version.print_version()
        sys.exit(0)

    # Get the configuration storage loocation
    config_store = tootgroup_tools.configuration_management.setup_configuration_store() 

    # Get the Mastodon account handle the script is running for.
    config_store["group_name"] = commandline_arguments["group_name"]
    group_name = config_store["group_name"]

    # Get and validate configuration from the config file.
    my_config = tootgroup_tools.configuration_management.parse_configuration(config_store)

    # If the "catch-up" commandline argument has been given, reset the last seen
    # ID so that tootgroup.py only updates its according config value without
    # retooting anything.
    if commandline_arguments["catch_up"]:
        my_config[group_name]["last_seen_id"] = "catch-up" 
    
    # Create Mastodon API instance.
    masto = mastodon.Mastodon(
        client_id = config_store["directory"] + my_config[group_name]["client_id"],
        access_token = config_store["directory"] + my_config[group_name]["access_token"],
        api_base_url = my_config[group_name]["mastodon_instance"]
    )
    
    try:
        # Get the group account information.
        # This connects to the Mastodon server for the first time at
        # every tootgroup.py's run.
        my_account = {
            "username": masto.account_verify_credentials().username, 
            "id": masto.account_verify_credentials().id, 
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

    # TODO: Check if account IDs are unique across all mastodon
    # servers Get group member IDs. They could not be fetched directly while
    # connecting to the Mastodon server.
    for member in masto.account_following(my_account["id"]):
        my_account["group_member_ids"].append(member.id)
    
    # Do we accept direct messages, public retoots, both or none? This
    # can be set in the configuration.
    accept_DMs = my_config[group_name].getboolean("accept_DMs")
    accept_retoots = my_config[group_name].getboolean("accept_retoots")
    dm_visibility = my_config[group_name]["dm_visibility"]
    
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
        get_notifications = masto.notifications(max_id = max_notification_id)
        
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
        if my_config[group_name]["last_seen_id"] == "catch-up":
            my_config[group_name]["last_seen_id"] = str(latest_notification_id)
            config_store["write_NEW"] = True
            print("Caught up to current timeline. Run again to start group-tooting.")
        
        for notification in get_notifications:
            max_notification_id = notification.id
            
            if (notification.id > int(my_config[group_name]["last_seen_id"]) and
                    notification_count < max_notifications):
                my_notifications.append(notification)
            else:
                get_more_notifications = False
                break
            
            notification_count += 1
    
    # If there have been new notifications since the last run, update "last_seen_id"
    # and write config file to persist the new value.
    if latest_notification_id > int(my_config[group_name]["last_seen_id"]):
        my_config[group_name]["last_seen_id"] = str(latest_notification_id)
        config_store["write_NEW"] = True
    
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
                        if not commandline_arguments["dry_run"]:
                            masto.status_reblog(notification.status.id)
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
                    # Get the group account's @username
                    account_username = "@" + my_account["username"]

                    # Only continue if the DM starts with the group account's @username
                    if new_status.startswith(account_username):
                        # Remove the group account's @username from the text
                        new_status = re.sub(account_username, "", new_status)
                        # "un-escape" HTML special characters
                        new_status = html.unescape(new_status)
                        if not commandline_arguments["dry_run"]:
                            # Repost as a new status
                            masto.status_post(
                                new_status,
                                media_ids = media_toot_again(notification.status.media_attachments,
                                    masto),
                                sensitive = notification.status.sensitive,
                                visibility = dm_visibility,
                                spoiler_text = notification.status.spoiler_text
                            )
                            print("Newly posted from DM with notification ID: " + str(notification.id))
                        else:
                            print("DRY RUN - would have newly posted from DM with notification ID: "
                                + str(notification.id))

                    # If the DM does not start with the group account's @username it will not
                    # trigger a new toot. Notify the originating user why this happened instead!
                    else:
                        if not commandline_arguments["dry_run"]:
                            new_status = ("@" + notification.account.acct + "\n"
                            "Ohai! - This is a notification from your friendly tootgroup.py bot.\n\n"
                            "Your message has not been converted to a new group toot because it did "
                            "not start with @" + my_account["username"] + "\n\n"
                            "Remember to put @" + my_account["username"] + " at the very beginning if "
                            "you want to create a new group toot.")
                            masto.status_post(
                                new_status,
                                in_reply_to_id = notification.status.id,
                                visibility = "direct",
                            )
                            print("Not posted from DM with notification ID: " + str(notification.id), end="")
                            print(". It did not start with @" + my_account["username"] + "!")
                        else:
                            print("DRY RUN - received DM with notification ID: "
                                + str(notification.id) +
                                ", but it did not begin with @" + my_account["username"] + "!")
    
    # There have been changes requiring to persist the new configuration
    # but not in a dry-run condition
    if config_store["write_NEW"] and not commandline_arguments["dry_run"]:
        tootgroup_tools.configuration_management.write_configuration(config_store, my_config)
    
    print("Successful tootgroup.py run for " + "@" + my_account["username"] +
        " at " + my_config[group_name]["mastodon_instance"])


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


# Start executing main() function if the script is called from a command line
if __name__=="__main__":
    main()
