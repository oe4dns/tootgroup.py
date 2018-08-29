tootgroup.py - emulate group accounts on Mastodon.
==================================================


What is this?
-------------

Some social media platforms allow groups of users to post into a unified "group"
timeline/instance/whatever you want to call it. This is currently not possible
on Mastodon without giving all members full login credentials to a group.
tootgroup.py is an attempt to solve this specific use case.


How does it work?
-----------------

tootgroup.py has to be set up on a computer and run periodically. It reads the
notifications from the Mastodon account it is connected to and filters them for
messages to repost. There are two methods of creating a group post. One or both
of them can be enabled or disabled during the setup procedure.

1. Public mentions of group members are retooted if they preceed the group's
name with an Exclamation Mark like "!@mastodon"

2. tootgroup.py can also look for direct messages from group members. It then
extracts the status text as well as media files and creates a new public toot
directly from the group account. The originating user will not be shown publicly
but can still be seen by all group and instance administrators.

If both repost methods are disabled, tootgroup.py will still run but not repost
anything.


How to set up?
--------------

tootgroup.py is still largely untested and in development. I will help you with
setup by asking all information it needs when you run it from the commandline
for the first time. Still it might help if your're somewhat comfortable with Python
scripting and the commandline in general.

1. You require https://github.com/halcy/Mastodon.py to run.
Install it via your operating system's package manager, pip or even manually

2. You need an account on any Mastodon instance/server that will act as your
group account. Think about if you should mark it as a "Bot".

3. Run tootgroup.py from the command line in a directory that it can write to.
Input all required information and register with your Mastodon instance.

4. tootgroup.py will ask you for all needed setup information and try to get
it right by connecting with the Mastodon server. If it cannot do so, it will tell
you and you can try again. When successful, tootgroup.py will write the
configuration to its .conf file and read it from there next time you run the script.
Every successful run will print an according message to the command line.

5. Test the funcionality by sending direct messages and "!@mentions" to your
group while manually running tootgroup.py. See if everything works as expected.
If it does, you can run the script periodically via cron and enjoy groop-tooting!

    Here an example for a crontab entry that runs tootgroup.py every two minutes:
    
    `*/2 * * * * cd /home/username/bin/ && python3 tootgroup.py`




Planned Features and Whishlist items
------------------------------------

##### TODO: Error handling
      Currently there is not much... wich is still bad

##### TODO: file management
      Currently tootgroup.py simply runs from a directory where it will also
      keep all its configuration specific and temporary files. In Linux things
      will be moved to a user specific dot-directory and maybe the /tmp folder.
      for other platforms look at the "multi-platform" task.

##### TODO: multi-user
      create configuration files for separate users making it possible to
      use tootgroup.py in parallel for multiple groups without hardcoding
      anything in it.

##### TODO: multi-platform
      While Python is pretty platform independent, tootgroup.py has only been
      tested on Linux using Python 3. That concerns mostly the user configuration
      as well as (temporary) file management.

##### TODO: pagination
      If there are too many notifications returned from Mastodon, they will be
      paginated. This could lead to direct messages being missed by tootgroup.py
      in a heavy use scenario (unlikely) or if it is being spammed acively (denial
      of service attack). Iterating over paginated returns is needed.

##### TODO: push-notifications feasible?
      Look into push notifications so that tootgroup.py would not have to be
      run via cron periodically


