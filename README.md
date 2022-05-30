`tootgroup.py` - emulate group accounts on Mastodon and Pleroma
=================================================

What is this?
-------------

Some social media platforms allow groups of users to post into a unified "group"
timeline/instance/whatever you want to call it. This is currently not possible
on Mastodon or Pleroma without giving all members full login credentials to a
group. `tootgroup.py` is an attempt to solve this specific use case.

tootgroup.py groups can be hosted on Mastodon or Pleroma. But you can post
TO the group FROM any ActivityPub service although there might be some
incompatibilities. Currently Mastodon, Pleroma and Friendica are tested platforms
for posting TO the group. More tests are welcome!

How does it work?
-----------------

`tootgroup.py` has to be set up on a computer and run periodically. It reads the
notifications from the Mastodon/Pleroma account it is connected to and filters
them for messages to repost. There are two methods of creating a group post. One
or both of them can be enabled during the setup procedure.

1. Public mentions of group members are boosted if they preceed the group's
   name with an Exclamation Mark like "!@mastodon". For for posts originating
   from Friendica the correct syntax is "!mastodon".

2. `tootgroup.py` can also look for direct messages from group members. If the
   group is @mentioned at the very beginning, The message will be reposted as
   a new public toot originating directly from the group account. The status
   text as well as media files are included. The originating user will not be
   shown publicly. (It can still be seen by all group and instance
   administrators tough!)

If both repost methods are disabled, `tootgroup.py` will still run but not repost
anything.

But how to simply use it?
-------------------------

### Mastodon/Pleroma

1. Write a message that should be boosted by the group:
   Just include "!@group_name" anywhere in the toot.

   EXAMPLE: "OHAI! just found that !@mastodon thingie!"

2. Write a message that should appear as a new post from the group:
   Put "@group_name" at the very beginning of a direct/private message.

   EXAMPLE: "@mastodon HERE BE THE MESSAGE TEXT"

### Friendica

Because of its history and much more flexible nature, things are a bit different
and maybe even a bit more complicated when posting from Friendica. Nevertheless
this is fully supported, tested and in daily use.

1. Write a message that should be boosted by the group:
   Friendica handles the Exclamation Mark in a special way because it is also
   used to address the Friendica Forum functionality. Thus you have to omit the
   "@" like shown below

   EXAMPLE (from Friendica): "OHAI! just found that !mastodon thingie!"

2. Write a message that should appear as a new post from the group:
   You can send a direct message by limiting the visibility of a "normal" post
   or by using the personal message menu. The second method does not work with
   images though, so creating normal posts with limited visibility is preferred.
   You should always leave the Title/Subject field empty, it might not work as
   expected otherwise. Put "@group_name" at the very beginning of a
   direct/private message.

   EXAMPLE: "@mastodon HERE BE THE MESSAGE TEXT"

How to set up?
--------------

The easiest way to install `tootgroup.py` is via PyPI, the Python Package Index.
Use `pip3 install tootgroup.py` to install it as well as all its dependencies.

It is also possible to download the script manually from the GitHub repository at
<https://github.com/oe4dns/tootgroup.py> In that case the necessary dependencies
have to be provided too:

`tootgroup.py` requires <https://github.com/halcy/Mastodon.py> as well as
<https://github.com/ActiveState/appdirs> to run. Install them via your
operating system's package manager, pip or even manually.

`tootgroup.py` will guide you through setup by asking all information it needs
when you run it from the commandline for the first time. Being somewhat
comfortable with Python scripting and the commandline in general might help
if difficulties should appear.

1. You need an account on any Mastodon or Pleroma instance that will act as
   your group account. Think about if you should mark it as a "Bot".

2. Run `tootgroup.py` from the command line.

3. `tootgroup.py` will ask you for all needed setup data and try to get them
   right by connecting to the Mastodon/Pleroma server. If it cannot do so, it
   will tell you and you can retry. When successful, `tootgroup.py` will write
   the configuration to its tootgroup.conf file and read it from there next
   time you run the script.

   The place for storing configuration is operating system dependent but will be
   shown during the first-run/setup phase. A local tootgroup.conf file placed
   next to the `tootgroup.py` script will override these settings though and can
   be used for development or testing purposes.

4. If you want to set up `tootgroup.py` for more than one group, you can run it
   again while specifying the "--group GROUP_HANDLE" flag. This will then
   generate an independent configuration that will be read each time you call
   `tootgroup.py` using this name. If you don't specify any group name, the
   handle "default" is created and used automatically

5. Test the funcionality by sending direct messages and "!@mentions" to your
   group while running `tootgroup.py` manually. See if things work as expected.
   The script will print an according message after each successful run.
   If everything works, run the script periodically via cron and enjoy
   groop-tooting!

   Here is an example for a crontab entry that runs `tootgroup.py` every two minutes:

   `*/2 * * * * /path/to/tootgroup.py --group default`

6. There is also the "-d" or "--dry-run" commandline flag that prevents any toots.
   You can use it to test what would be posted by the script.

   Use "-h" or "--help" for more information about all available options
