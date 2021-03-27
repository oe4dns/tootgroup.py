## Manages the applications config file storage location, reading
## and writing.

import appdirs
import os
import sys


def setup_configuration_store():
    """Search for the configuration file location. Start with the
    skript's home directory and try the OS specific user configuration
    directory next. Local takes precedence but if no configuration
    is found, the new one will be created in the OS specific user
    config path if possible. If that fails, the local directory will
    again be used as a last resort. This is to ensure
    backwards-compatibility and to enable local overrides for
    development/testing.

    Returns a dictinary containing  basic information about how to
    find the configuration. Some dictionary values will be populated
    later (see below for available fields)"""

    config_store = {'filename': '',
                    'directory': '',
                    'group_name': '',
                    'write_NEW' : True }

    # Get name and path of the running application. It is used to
    # determine its configuration storage path
    stack = sys._getframe(1).f_globals  # get caller's globals
    application_namepath = stack['__file__']
    application_path, application_name = os.path.split(application_namepath)
    application_path = application_path + '/'

    # The config file is named after the application with
    # the extension is changed from ".py" to ".conf"
    # Only the last occurence of ".py" is replaced!
    old_ext = '.py'
    new_ext = '.conf'
    config_filename = new_ext.join(application_name.rsplit(old_ext,1))
    config_store['filename'] = config_filename

    local_path = application_path
    os_user_config_path = appdirs.AppDirs(application_name).user_data_dir + "/"
    config_store['directory'] = local_path 

    # Is there a config file in the tootgroup.py directory?
    if os.path.isfile(local_path + config_filename):
        config_store['write_NEW'] = False
        print("Found local configuration and using it...")

    # Is there a config file in the system's user config directory?
    elif os.path.isfile(os_user_config_path + config_filename):
        config_dir = os_user_config_path
        config_store['write_NEW'] = False
        # This is the default, do not output anything
    
    # Did not find any config file, default to user config dir!
    else:
        config_dir = os_user_config_path
        # Create config dir if it does not exist yet
        try:
            os.makedirs(config_dir, exist_ok=True)
            print("No configuration found!")
            print("tootgroup.py will continue to run but first " +
            "ask for all information it requires...\n" +
            "Configuration will then be stored under " +
            config_dir + "\n")
        except Exception:
            # Cannot create config directory, have to use the
            # tootgroup.py dir instead 
            config_dir = local_path
            print("No configuration found!")
            print("tootgroup.py will continue to run but first " +
            "ask for all information it requires...\n" +
            "Configuration will then be stored under " +
            config_dir + "\n")

    return(config_store)
