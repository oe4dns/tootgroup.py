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

from mastodon import Mastodon



# TODO: clean and easy first run/setup, asking for missing config details
## ONLY FOR FIRST RUN - this sets up app credentials for tootgroup.py
## UNCOMMENT ONCE FOR SETUP
#import sys
#
## Register app - only once!
#
# my_mastodon_instance='YOUR_INSTANCE_HERE'
#
#Mastodon.create_app(
#     'tootgroup.py',
#     api_base_url = my_mastodon_instance,
#     to_file = 'tootgroup_clientcred.secret'
#)
#
## Log in - either every time, or use persisted
#mastodon = Mastodon(
#    client_id = 'tootgroup_clientcred.secret',
#    api_base_url = my_mastodon_instance
#)
#
#mastodon.log_in(
#    input("Username (e-Mail): "),
#    input("Password: "),
#    to_file = 'tootgroup_usercred.secret'
#)
#sys.exit(0)
## END OF SETUP BLOCK



# Execution starts here.
def main():
    
    # Configuration - to be read from config files while also
    # considering commandline flags
    # TODO: configparser and agparse!
    # TODO: standard storage place for config (and tmp files?)
    my_config_file = 'tootgroup.conf'
    
    #instantiate the ConfigParser class
    my_config = configparser.ConfigParser()
    my_config.read(my_config_file)
    
    my_mastodon_instance = my_config['default']['mastodon_instance']
    my_client_id = my_config['default']['client_id']
    my_access_token = my_config['default']['access_token']
    accept_DMs = my_config['default'].getboolean('accept_DMs')
    accept_retoots = my_config['default'].getboolean('accept_retoots')


    # Create Mastodon API instance
    mastodon = Mastodon(
        client_id = my_client_id,
        access_token = my_access_token,
        api_base_url = my_mastodon_instance
    )
    
    
    # Get the group account and all corresponding information
    # name, id, group members (== accounts followed by the group)
    # and their IDs
    my_account = {
        "username" : mastodon.account_verify_credentials().username, 
        "id" : mastodon.account_verify_credentials().id, 
        "group_members" : "", 
        "group_member_ids" : []
    }
    my_account["group_members"] = mastodon.account_following(my_account["id"])
    for member in my_account["group_members"]:
        my_account["group_member_ids"].append(member.id)

    
    # Get the time of the latest (re)toot from the group. Using it we
    # can determine which messages are new since last run.
    my_last_toot_time = mastodon.account_statuses(my_account["id"])[0].created_at
    
    # Get all notifications
    # TODO: check for pagination should the list become too long
    my_notifications = mastodon.notifications()

    # run through the notifications and look for retoot candidates
    for notification in my_notifications:
        
        # Only consider notifications that happened after the groups last toot
        # We have to use the time of notification and not the "status" directly since
        # not all notification types do have a status.
        if notification.created_at > my_last_toot_time:
            
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
                        
                        # Remove html tags from the status content
                        new_status = re.sub("<.*?>", "", notification.status.content)
                        # Remove @metafunk from the text
                        new_status = re.sub("@metafunk", "", new_status)
                        
                        # Repost as a new status
                        mastodon.status_post(
                            new_status,
                            media_ids = media_toot_again(notification.status.media_attachments, mastodon),
                            sensitive = notification.status.sensitive,
                            visibility = "public",
                            spoiler_text = notification.status.spoiler_text
                        )




def media_toot_again(orig_media_dict, mastodon_instance):
    """Re-upload media files to Mastodon for use in another toot.
    
    'orig_media_dict' - extracted media files from the original toot
    'mastodon_instance' - needed to upload the media files again and create
    a new media_dict.
    
    Mastodon does not allow the re-use of already uploaded media files (images,
    videos) in a new toot. This function downloads all media files from a toot
    and uploads them again. It returns a dict formatted in a proper way to be
    used with the Mastodon.status_post() function."""
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



# Start executing main() function if the script is called from a command line
if __name__=="__main__":
    main()
