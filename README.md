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
notifications of the Mastodon account it is connected to and filters them for
messages to repost. There are two methods of creating a group post. One or both
of them can be enabled or disabled during configuration.

1. Public mentions of group members are retooted if they preceed the group's
name with an Exclamation Mark like "!@mastodon"

2. tootgroup.py can also look for direct messages from group members. It then
extracts the status text as well as media files and creates a new public toot
directly from the group account. The originating user will not be shown publicly
but can still be seen by the group and instance administrators.

If both repost methods are disabled, tootgroup.py will still run but not repost
anything.


How to set up?
--------------

tootgroup.py is still largely untested and in development. For the moment it has
to be set up and configured manually by a person who understands the code and
what it is doing. This will become MUCH MORE CONVINIENT in the future. 

1. You require https://github.com/halcy/Mastodon.py to run.
Install it via your operating system's package manager, pip or even manually

2. You need an account on any Mastodon instance/server that will act as your
group account. Think about if you should mark it as a "Bot".

3. At the beginning of the tootgroup.py script change:
```my_mastodon_instance='TO_YOUR_MASTODON_INSTANCE'```

4. At the beginning of the tootgroup.py script you will also find the
registration/first run code block. It is marked thus. You have to have your login
and password ready. With that the tootgroup.py script can register itself as an
authorised app in the Mastodon account settings.

5. Run tootgroup.py from the command line in a directory that it can write to.
Input all required information and register with your Mastodon instance.

6. When setup is done you MUST comment-out the setup code block again or otherwise
tootgroup.py will re-register every time it is run! If this happens, you can still
clean out all your allowed apps from your Mastodon account setings but try to avoid
that.

7. Test the funcionality by sending direct messages and "!@mentions" to your
group while manually running tootgroup.py. See if everything works as expected.
If it does, you can run the script periodically via cron and enjoy groop-tooting!




Planned Features and Whishlist items
------------------------------------

##### TODO: autoinstall/autoconfigure
      Check which configuration details are missing on startup and
      query the user. That way tootgroup.py can be started from the
      command line and will ask for all missing configuration details.
      If nothing is missing, the script will simply do its task and
      can then be automated with cron.

##### TODO: Error handling
      Currently there is none... wich is bad

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


