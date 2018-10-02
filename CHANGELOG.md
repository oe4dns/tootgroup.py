# Change Log

## [0.5] 2018-??-??
- Read commandline flags with agparser
- Multigroup configuration from one skript



## [0.4.1] 2018-10-02
### FIXED
- Retoots of direct messages do now keep their linebreaks
- Removed hardcoded @groupname

## [0.4] 2018-08-29
###ADDED
- Read and persist configuration with configparser
- Detect problems with configuration and get user input for corrections
- First-run/Install feature. Detect missing configuration and ask user for all
necessary setup details.

## [0.3] 2018-08-28
### CHANGED
- Retoot mode is no longer triggered by using a specific hastag, but by preceding
the mention with an Exclamation Mark like "!@mastodon"
- Code refactoring and cleanup. tootgroup.py behaves now more like a real
commandline application.

## [0.2] - 2018-08-24
### Added
- Configurable retoot mode
Public mentions from group members are now retooted if they include a trigger
hashtag. That way thei will point to the originating user. Direct messages are
sent as new toots just like before, but the originating user will not be shown
in that case. This is NOT a privacy feature since the group admin will still see
who created a specific message. However, it can be handy for some use cases.
Both options can be enabled or disabled during setup.

## [0.1] - 2018-08-19
### Initial commit
- Basic proof of concept.
- Manual installation and setup required
- Create new toots from direct messages of group members only
