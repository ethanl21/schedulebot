import os
import sys
import random
from configparser import ConfigParser


def get_config():
    if 'DYNO' in os.environ:  # If deployed to Heroku
        token = os.getenv('token')
        prefix = os.getenv('prefix')
    else:  # If deployed locally (testing)
        cfg = ConfigParser()
        try:
            cfg.read('config.ini')
                # read vars
            token = cfg['keys']['token']
            prefix = cfg['bot_config']['command_prefix']
        except KeyError as err:  # generate a new config.ini if not found
            cfg['keys'] = {
                'token': 'your token here'
            }
            cfg['bot_config'] = {
                'command_prefix': '!'
            }

            with open('config.ini', 'w') as config_file:
                cfg.write(config_file)
                print(
                f"Config file generated at {os.path.realpath(config_file.name)}.")
                print(
                'Replace the values in the file with your desired values and run the program again.')
            sys.exit()

        else:  # Running locally and config file was found
            token = cfg['keys']['token']
            prefix = cfg['bot_config']['command_prefix']

        return token, prefix
    

def random_color():
    return random.randint(0,16777215)
