`tootgroup.py` - emulate group accounts on Mastodon
=================================================

What is this?
-------------

Some social media platforms allow groups of users to post into a unified "group"
timeline/instance/whatever you want to call it. This is currently not possible
on Mastodon without giving all members full login credentials to a group.
`tootgroup.py` is an attempt to solve this specific use case.

How does it work?
-----------------

`tootgroup.py` has to be set up on a computer and run periodically. It reads the
notifications from the Mastodon account it is connected to and filters them for
messages to repost. There are two methods of creating a group post. One or both
of them can be enabled during the setup procedure.

1. Public mentions of group members are boosted if they preceed the group's
   name with an Exclamation Mark like "!@mastodon"

2. `tootgroup.py` can also look for direct messages from group members. It then
   extracts the status text as well as media files and creates a new public toot
   directly from the group account. The originating user will not be shown publicly
   but can still be seen by all group and instance administrators.

If both repost methods are disabled, `tootgroup.py` will still run but not repost
anything.

How to set up?
--------------

`tootgroup.py` will help you with setup by asking all information it needs when
you run it from the commandline for the first time. Being somewhat comfortable
with Python scripting and the commandline in general might help tough, if
difficulties should appear. While `tootgroup.py` is feature complete already,
it is still in beta and needs more testing.

1. You require <https://github.com/halcy/Mastodon.py> as well as
   <https://github.com/ActiveState/appdirs> to run. Install them via your
   operating system's package manager, pip or even manually

2. You need an account on any Mastodon instance/server that will act as your
   group account. Think about if you should mark it as a "Bot".

3. Run `tootgroup.py` from the command line.

4. `tootgroup.py` will ask you for all needed setup data and try to get them
   right by connecting to the Mastodon server. If it cannot do so, it will
   tell you and you can retry. When successful, `tootgroup.py` will write the
   configuration to its tootgroup.conf file and read it from there next time
   you run the script.

   The standard configuration store is operating system dependent but will be
   shown during the first-run/setup phase. A local tootgroup.conf file placed
   next to the `tootgroup.py` script will override these settings tough and can
   be used for testing or other purposes.

5. If you want to set up `tootgroup.py` for more than one group, you can run it
   again while specifying the "--group GROUP_HANDLE" flag. This will then
   generate an independent configuration that will be read every thime you call
   `tootgroup.py` using this name. If you don't specify any, the handle "default"
   is created and used automatically

6. Test the funcionality by sending direct messages and "!@mentions" to your
   group while running `tootgroup.py` manually. See if things work as expected.
   The script will print an according message after each successful run.
   If everything works, run the script periodically via cron and enjoy
   groop-tooting!

   Here is an example for a crontab entry that runs `tootgroup.py` every two minutes:

   `*/2 * * * * /path/to/tootgroup.py --group default`

7. There is also the "-d" or "--dry-run" commandline flag that prevents any toots.
   You can use it to test what would be posted by the script.

   Use "-h" or "--help" for more information about all available options

Planned Features and Whishlist items
------------------------------------

### TODO: Error handling - v0.8

    Currently there is not much... which is still bad

### TODO: Testing - v0.9

    Especially on platforms other than Linux