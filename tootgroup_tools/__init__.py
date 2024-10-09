from tootgroup_tools import commandline_arguments, configuration_management


def compare_ids(current_notification_id, stored_notification_id):
    """Fediverse services use different kinds of notification IDs. Some
    use integers counting up from 0, some lexicographically sortable strings
    etc. This functin can distinguish and return the correct answer

    Parameters:
    current_notification_id: ID of the currently processed notification
    stored_notification_id: Stored ID value of the last notification that was
                            processed in the previous run.

    Returns: True if the current notification is newer, False if not.
    """

    # Try castint to an integer. If it works, it probably is an integer
    # and can be compared as such.
    try:
        cur = int(current_notification_id)
        sto = int(stored_notification_id)
        if cur > sto:
            return True
        else:
            return False

    # If casting to an integer fails, threat everything as a string which
    # is then lexicographically sorted.
    except:
        cur = str(current_notification_id)
        sto = str(stored_notification_id)
        if cur > sto:
            return True
        else:
            return False
