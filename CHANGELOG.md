# Change Log

## [0.7] 20??-??-??

Temporary file storage and cross platform checks
Ketchup

## [0.6] 2018-11-08

### ADDED

- Pagination. Fetching notifications can give paged results if there are too
  many to return at once. `tootgroup.py` can now take care of that and also limit
  the maximum fetched notifications count.

### CHANGED

- Further improved shared mode. No more difference necessary between it and
  exclusive account access by `tootgroup.py`
  Notification IDs are now used to determine which ones are new and have to be considered for posting.

## [0.5.2] 2018-10-31

### FIXED

- Media upload was broken due to change in Mastodon's media.url

## [0.5.1] 2018-10-12

### FIXED

- Retoots of direct messages do no longer show HTML-escaped special characters

## [0.5] 2018-10-12

### ADDED

- Read commandline flags with agparser
- Added --user flag to configure and use multiple accounts
- When sharing access to a group, `tootgroup.py` does no longer look for the last
  time it wrote anything to the group to determine what has happened since. In
  that case its persists timestamps and checks when the last run has happened to
  search for any new toots or direct messages to process. This is needed because
  any toots from other sources would cause `tootgroup.py` to miss notifications that
  happened between it and tootgroup's last run. This feature writes the config
  file to the disk every thime `tootgroup.py` is run and for that reason it is only
  activated if a shared account requires it.

## [0.4.1] 2018-10-02

### FIXED

- Retoots of direct messages do now keep their linebreaks
- Removed hardcoded @groupname

## [0.4] 2018-08-29

### ADDED

- Read and persist configuration with configparser
- Detect problems with configuration and get user input for corrections
- First-run/Install feature. Detect missing configuration and ask user for all
  necessary setup details.

## [0.3] 2018-08-28

### CHANGED

- Retoot mode is no longer triggered by using a specific hastag, but by preceding
  the mention with an Exclamation Mark like "!@mastodon"
- Code refactoring and cleanup. `tootgroup.py` behaves now more like a real
  commandline application.

## [0.2] - 2018-08-24

### Added

- Configurable retoot mode
  Public mentions from group members are now boosted if they include a trigger
  hashtag. That way they will point to the originating user. Direct messages are
  sent as new toots just like before, but the originating user will not be shown
  in that case. This is NOT a privacy feature since the group admin will still see
  who created a specific message. However, it can be handy for some use cases.
  Both options can be enabled or disabled during setup.

## [0.1] - 2018-08-19

### Initial commit

- Basic proof of concept.
- Manual installation and setup required
- Create new toots from direct messages of group members only
