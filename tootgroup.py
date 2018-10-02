#!/bin/python3

## tootgroup.py
## Version 0.4
##
##
## Andreas Schreiner
## @andis@chaos.social
## andreas.schreiner@sonnenmulde.at
##
## License: General Public License Version 3
## See attached LICENSE file.
##

import configparser
import os
import re
import requests
import sys

from mastodon import Mastodon



# Execution starts here.
def main():
    
    # TODO: agparse! - commandline flags
    # TODO: standard storage place for config (and tmp files?)
    # TODO: remove ramaining temp files from last run if the script did not close cleanly
    my_config_file = 'tootgroup.conf'
    my_group_name = 'default'
        
    # Get and validate configuration from the config file.
    my_config = parse_configuration(my_config_file, my_group_name)  
    
    # Create Mastodon API instance
    mastodon = Mastodon(
        client_id = my_config[my_group_name]['client_id'],
        access_token = my_config[my_group_name]['access_token'],
        api_base_url = my_config[my_group_name]['mastodon_instance']
    )
       
    try:
        # Get the group account and all corresponding information
        # name, id, group members (== accounts followed by the group)
        # their IDs and the time of the group's last toot.
        #
        # This connects to the Mastodon server for the first time - catch any
        # excpetions that may occur from that here.
        my_account = {
            "username" : mastodon.account_verify_credentials().username, 
            "id" : mastodon.account_verify_credentials().id, 
            "group_members" : "", 
            "group_member_ids" : [], 
            "last_toot_time" :  ""
        }
    except Exception as e:
        print("")
        print(e)
        print("\n########################################################")
        print("tootgroup.py could not connect to the Mastodon server.")
        print("If you know that it is running, there might be a")
        print("problem with our local configuration.")
        print("\nDelete tootgroup.py's config file and re-run the script")
        print("for a new setup.")
        print("########################################################\n")
        sys.exit(0)
    # Extract account information that could not be fetched directly    
    my_account["group_members"] = mastodon.account_following(my_account["id"])
    for member in my_account["group_members"]:
        my_account["group_member_ids"].append(member.id)
    # FIXME: This throws an Index Error if the account has never tooted anything!
    # Only a problem with a totally new account but should be fixed before final relase.
    my_account["last_toot_time"]  = mastodon.account_statuses(my_account["id"])[0].created_at
    
    # Do we accept direct messages, public retoots, both or none? This
    # can be set in the configuration.
    accept_DMs = my_config[my_group_name].getboolean('accept_DMs')
    accept_retoots = my_config[my_group_name].getboolean('accept_retoots')
        
    # Get all notifications
    # TODO: check for pagination should the list become too long
    my_notifications = mastodon.notifications()

    # run through the notifications and look for retoot candidates
    for notification in my_notifications:
        
        # Only consider notifications that happened after the groups last toot
        # We have to use the time of notification and not the "status" directly since
        # not all notification types do have a status.
        if notification.created_at > my_account["last_toot_time"]:
            
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
                            mastodon.status_reblog(notification.status.id)
        
                # Is reposting of direct messages configured? - if yes then:
                # Look for direct messages
                if accept_DMs:
                    if notification.type == "mention" and notification.status.visibility == "direct":
                        
                        # Remove html tags from the status content but keep linebreaks
                        new_status = re.sub("<br />", "\n", notification.status.content)
                        new_status = re.sub("</p><p>", "\n\n", new_status)
                        new_status = re.sub("<.*?>", "", new_status)
                        # Remove the @username from the text
                        rm_username = "@" + my_account["username"]
                        new_status = re.sub(rm_username, "", new_status)
                        
                        # Repost as a new status
                        mastodon.status_post(
                            new_status,
                            media_ids = media_toot_again(notification.status.media_attachments, mastodon),
                            sensitive = notification.status.sensitive,
                            visibility = "public",
                            spoiler_text = notification.status.spoiler_text
                        )
                        
    print("Successful tootgroup.py run for " + "@" + my_account["username"] +
        " at " + my_config[my_group_name]['mastodon_instance'])




def media_toot_again(orig_media_dict, mastodon_instance):
    """Re-upload media files to Mastodon for use in another toot.
    
    'orig_media_dict' - extracted media files from the original toot
    'mastodon_instance' - needed to upload the media files again and create
    a new media_dict.
    
    Mastodon does not allow the re-use of already uploaded media files (images,
    videos) in a new toot. This function downloads all media files from a toot
    and uploads them again.
    
    It returns a dict formatted in a proper way to be used by the 
    Mastodon.status_post() function."""
    new_media_dict = []
    for media in orig_media_dict:
        media_data = requests.get(media.url).content
        # TODO: temporary file maganement needed here
        filename = os.path.basename(media.url)
        with open(filename, "wb") as handler: # use "wb" instead of "w" to enable binary mode (needed on Windows)
            handler.write(media_data)
        new_media_dict.append(mastodon_instance.media_post(filename, description=media.description))
        os.remove(filename)
    return(new_media_dict)



def new_credentials_from_mastodon(group_name, config):
    """Register tootgroup.py at a Mastodon server and get user credentials.
    
    'group_name' points to the current groups settings in the config file
    'config' the configuration as read in from configparser
    
    This will be run if tootgroup.py is started for the first time, if its
    configuration files have been deleted or if some elements of the
    configuration are missing.
    TODO: catch login/register errors and retry
    """
    # Register tootgroup.py app at the Mastodon server
    try:
        Mastodon.create_app(
            'tootgroup.py',
            api_base_url = config[group_name]['mastodon_instance'],
            to_file = config[group_name]['client_id']
        )
        # Create Mastodon API instance
        mastodon = Mastodon(
            client_id = config[group_name]['client_id'],
            api_base_url = config[group_name]['mastodon_instance']
        )
    except Exception as e:
        print("")
        print(e)
        print("\n###################################################################")
        print("The Mastodon instance URL is wrong or the server does not respond.")
        print("tootgroup.py will exit now. Run it again to try once more!")
        print("###################################################################\n")
        sys.exit(0)
 
    # Log in once with username and password to get an access token for future logins.
    # Ask until login succeeds or at most 3 times before the skript gives up.
    i = 0
    while i < 3:
        i+=1
        try:
            mastodon.log_in(
                input("Username (e-Mail): "),
                input("Password: "),
                to_file = config[group_name]['access_token']
            )
            break
        except Exception as e:
            print("\nUsername and/or Password did not match!")
            if i <3:
                print("Please enter them again.\n")
            else:
                print("tootgroup.py will exit now. Run it again to try once more!\n")
                sys.exit(0)




def parse_configuration(config_file,  group_name):
    """Read configuration from file, handle first-run situations and errors
    
    'config_file' the path to the configuration file
    'group_name' determines the section to be read by configparser
    
    parse_configuration() uses Pyhon's configparser to read and interpret the
    config file. It will detect a missing config file or missing elements a and
    then try to solve problems by asking the user for more information. This
    does also take care of a first run situation where nothing is set up yet and
    in that way act as an installer!
    
    parse_configuration should always return a complete and usable configuration"""
    config = configparser.ConfigParser()
    config.read(config_file)
    get_new_credentials = False
    write_new_config = False
    
    # Is there already a section for the current tootgroup.py
    # group. If not, create it now.
    if not config.has_section(group_name):
        config[group_name] = {}
        write_new_config = True
    
    # Do we have a mastodon instance URL? If not, we have to
    # ask for it and register with our group's server first.
    if not config.has_option(group_name,  'mastodon_instance'):
        config[group_name]['mastodon_instance'] = ""
    if config[group_name]['mastodon_instance'] == "":
        config[group_name]['mastodon_instance'] = input("Enter the "
            "URL of the Mastodon instance your group account is "
            "running on: ")
        get_new_credentials = True
        write_new_config = True
    
    # Where can the client ID be found and does the file exist?
    # If not, re-register the client.
    if not config.has_option(group_name,  'client_id'):
        config[group_name]['client_id'] = ""
    if config[group_name]['client_id'] == "":
        config[group_name]['client_id'] = group_name + "_clientcred.secret"
        get_new_credentials = True
        write_new_config = True
    if not os.path.isfile(config[group_name]['client_id']):
        get_new_credentials = True
    
    # Where can the user access token be found and does the file exist?
    # If not, re-register the client to get new user credentials
    if not config.has_option(group_name,  'access_token'):
        config[group_name]['access_token'] = ""
    if config[group_name]['access_token'] == "":
        config[group_name]['access_token'] = group_name + "_usercred.secret"
        get_new_credentials = True
        write_new_config = True
    if not os.path.isfile(config[group_name]['access_token']):
        get_new_credentials = True
    
    # Should tootgroup.py accept direct messages for reposting?
    if not config.has_option(group_name,  'accept_dms'):
        config[group_name]['accept_dms'] = ""
    if (config[group_name]['accept_dms'] == "") or (config[group_name]['accept_dms'] not in ('yes',  'no')):
        str = ""
        while True:
            str = input("Should tootgroup.py repost direct messages from group users? [yes/no]: ")
            if str.lower() not in ('yes',  'no'):
                print("Please enter 'yes' or 'no'!")
                continue
            else:
                break
        config[group_name]['accept_dms'] = str.lower()
        write_new_config = True
    
    # Should tootgroup.py accept public mentions for retooting?
    if not config.has_option(group_name,  'accept_retoots'):
        config[group_name]['accept_retoots'] = ""
    if (config[group_name]['accept_retoots'] == "") or (config[group_name]['accept_retoots'] not in ('yes',  'no')):
        str = ""
        while True:
            str = input("Should tootgroup.py retoot public mentions from group users? [yes/no]: ")
            if str.lower() not in ('yes',  'no'):
                print("Please enter 'yes' or 'no'!")
                continue
            else:
                break
        config[group_name]['accept_retoots'] = str.lower()
        write_new_config = True
    
    # Some registration info or credentials were missing - we have to register
    # tootgroup.py with our Mastodon server instance. (again?)
    if get_new_credentials:
        new_credentials_from_mastodon(group_name, config)
    
    # Have there been any changes to the configuration?
    # If yes we have to write them to the config file
    if write_new_config:
        with open(config_file, 'w') as configfile:
            config.write(configfile)
    
    # Configuration should be complete and working now - return it.
    return(config)



# Start executing main() function if the script is called from a command line
if __name__=="__main__":
    main()
