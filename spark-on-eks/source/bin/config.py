# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

from configparser import ConfigParser
import os.path as path

def ConfigSectionMap(section):
    dict1 = {}
    config = ConfigParser()
    config.read(path.join(path.dirname(__file__),"../../deployment/environment.cfg"))

    for key in config[section]:
        try:
            dict1[key] = config.get(section, key)
            if dict1[key] == -1:
                DebugPrint("skip: %s" % key)
        except:
            print("exception on %s!" % key)
            dict1[key] = None
    return dict1

