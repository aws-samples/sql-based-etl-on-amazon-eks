# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
#
import yaml
import urllib.request as request
import os.path as path
import sys
import re

def loadYamlRemotely(url, multi_resource=False):
    try:
        fileToBeParsed = request.urlopen(url)
        if multi_resource:
            yaml_data = list(yaml.full_load_all(fileToBeParsed))
        else:
            yaml_data = yaml.full_load(fileToBeParsed) 
        # print(yaml_data)  
    except:
        print("Cannot read yaml config file {}, check formatting."
                "".format(fileToBeParsed))
        sys.exit(1)
        
    return yaml_data 

def loadYamlLocal(yaml_file, multi_resource=False):

    fileToBeParsed=path.join(path.dirname(__file__), yaml_file)
    if not path.exists(fileToBeParsed):
        print("The file {} does not exist"
            "".format(fileToBeParsed))
        sys.exit(1)

    try:
        with open(fileToBeParsed, 'r') as yaml_stream:
            if multi_resource:
                yaml_data = list(yaml.full_load_all(yaml_stream))
            else:
                yaml_data = yaml.full_load(yaml_stream) 
            # print(yaml_data)    
    except:
        print("Cannot read yaml config file {}, check formatting."
                "".format(fileToBeParsed))
        sys.exit(1)
        
    return yaml_data 

def loadYamlReplaceVarRemotely(url, fields, multi_resource=False):
    try:
        with request.urlopen(url) as f:
            fileToBeReplaced = f.read().decode('utf-8')
            for searchwrd,replwrd in fields.items():
                fileToBeReplaced = fileToBeReplaced.replace(searchwrd, replwrd)

        if multi_resource:
            yaml_data = list(yaml.full_load_all(fileToBeReplaced))
        else:
            yaml_data = yaml.full_load(fileToBeReplaced) 
        # print(yaml_data)
    except request.URLError as e:
        print(e.reason)
        sys.exit(1)

    return yaml_data


def loadYamlReplaceVarLocal(yaml_file, fields, multi_resource=False):

    fileToBeReplaced=path.join(path.dirname(__file__), yaml_file)
    if not path.exists(fileToBeReplaced):
        print("The file {} does not exist"
            "".format(fileToBeReplaced))
        sys.exit(1)

    try:
        with open(fileToBeReplaced, 'r') as f:
            filedata = f.read()

            for searchwrd, replwrd in fields.items():
                filedata = filedata.replace(searchwrd, replwrd)
            if multi_resource:
                yaml_data = list(yaml.full_load_all(filedata))
            else:
                yaml_data = yaml.full_load(filedata) 
        # print(yaml_data)
    except request.URLError as e:
        print(e.reason)
        sys.exit(1)

    return yaml_data

# dataDict = {"{{region_name}}":"us-west-2","{{cluster_name}}":"_my_cluster","{{vpc_id}}": "testeste12345"}
# loadYamlLocal('../app_resources/jupyter-config.yaml', True)