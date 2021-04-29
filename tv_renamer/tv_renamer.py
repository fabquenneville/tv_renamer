#!/usr/bin/env python3
'''
    tv_renamer is a Python command line tool to rename TV episodes from an absolute to an aired order.
        * Rename all TV episodes in a file structure to the S00E00 standard
    ex:
    tv_renamer -options:print,noact -paths:/mnt/media/


    options:
        print       : print more detailed information
        noact       : dont act
        doubleep    : if video files contain two episodes each
        keepep      : keep the episode number
        preserve    : Preserve the filename except for a marker (*** by default)
'''

# TODO functions commands to be revised

import os
import sys
import re

def load_arguments():
    ''' Get/load command parameters

    Args:

    Returns:
        Dictionary (arguments): The command parameters passed by the users
    '''

    arguments = {
        "options":list(),
        "paths":list(),
        "marker":"***",
        "fseparator":" - ",
        "eseparator":" - ",
    }

    if len(sys.argv) >= 2:
        arguments["action"] = sys.argv[1]

    for arg in sys.argv:
        # Confirm with the user that he selected to delete found files
        if "-options:" in arg:
            arguments["options"] += arg[9:].split(",")
        elif "-paths:" in arg:
            if len(arg[7:].split(",")[0]) > 0:
                arguments["paths"] += arg[7:].split(",,")
        elif "-marker:" in arg:
            arguments["marker"] = arg[8:]
        elif "-fseparator:" in arg:
            arguments["fseparator"] = arg[12:]
        elif "-eseparator:" in arg:
            arguments["eseparator"] = arg[12:]
    
    paths = arguments["paths"]
    for n in range(len(paths)):
        if arguments["paths"][n] != "/":
            arguments["paths"][n] = arguments["paths"][n] + "/"

    return arguments

def get_content(parent_path, directories = False):
    ''' get the list of the content in a filepath

    Args:
        parent_path: the parent path to work on
        directories = False: If true only directories will be returned

    Returns:
        folderlist: Operations success
    '''
    if directories:
        folderlist = [ name for name in os.listdir(parent_path) if os.path.isdir(os.path.join(parent_path, name)) ]
    else:
        folderlist = os.listdir(parent_path)
    
    folderlist.sort()
    return folderlist

def replace_ss(parent_path, old = " ", new = "_"):
    ''' Replaces a specific substring trough a filetree

    Args:
        parent_path: the parent path to work on
        old: the substring to replace
        new: the new substring

    Returns:
        Bool: Operations success
    '''
    positive = False
    folderlist = get_content(parent_path)
    # print(folderlist)
    for n in range(len(folderlist)):
        # dont act on hidden folders/files
        if "." != folderlist[n][0]:
            newname = folderlist[n].replace(old, new, 1)
            # print(f'{parent_path + folderlist[n]} to {parent_path + newname}')
            os.rename(parent_path + folderlist[n],parent_path + newname)
            folderlist[n] = newname
            positive = True
    return positive

def add_numbering(arguments, parent_path, episode_per_file = 1):
    ''' This function will replace a marker (*** by default) by a searialized and delimited episode number while preserving the rest of the naming

    Example: calling add_numbering(arguments, parent_path) would result in:
        from:
        parent_path
            Season 01
                ***01.mkv
                ***02.mkv
                ...
            Season 02
                ***25.mkv
                26,mkv
                ...
            ...

        to:
        parent_path
            Season 01
                S01E01 - 01.mkv
                S01E02 - 02.mkv
                ...
            Season 02
                S02E01 - 25.mkv
                26,mkv
                ...
            ...

    Args:
        arguments: the options selected by the user
        parent_path: the parent path to work on
        episode_per_file: the number of episodes per file

    Returns:
        bool: Returns a positive if there was at least a match
    '''
    positive = False
    folderlist = get_content(parent_path, directories = True)
    for n in range(len(folderlist)):
        if len(re.findall('\d+', folderlist[n] )) <= 0:
            continue
        season_nb = re.findall('\d+', folderlist[n] )[0]
        episode_itt = 0
        part_itt = 0
        filelist = get_content(parent_path + folderlist[n])

        # get rid of non numbered files
        filelist = [item for item in filelist if len(re.findall('\d+', item))>0]
        
        # order the list by the fist number found in the name
        filelist.sort(key=lambda line: int(re.findall('\d+', line )[0]))
        numbers = [re.findall('\d+', line )[0] for line in filelist]
        lastnum = -1
        lastpart = 0
        for m in range(len(filelist)):
            # Get the first number in the filename  see its link to other files
            oldepnum = re.findall('\d+', filelist[m] )[0]
            newepnum = ""
            # If it is not the same episode number as the last file we start a new episode and reset the parts and start working
            if oldepnum != lastnum:
                episode_itt += 1
                part_itt = 0
            lastnum = oldepnum
            
            # Find and prepare the zeros before the actual season, episode and part numbers
            seasonzero = ""
            zero = ""
            partzero = ""

            # Select number of zeros in season number
            if int(season_nb) < 10 and season_nb[0] != "0":
                seasonzero = "0"

            # Select number of zeros in episode number
            if len(filelist) >= 100 and episode_itt < 10:
                zero = "00"
            elif len(filelist) >= 100 and episode_itt < 100:
                zero = "0"
            elif episode_itt < 10:
                zero = "0"

            # If there is more that one part to the episode use the multi-part filename template
            if len([i for i in numbers if i == oldepnum]) > 1:
                part_itt += 1
                
                # Select number of zeros in part number
                if part_itt < 10:
                    partzero = "0"
                
                newepnum += f'{arguments["fseparator"]}S{seasonzero}{season_nb}E{zero}{episode_itt} Part {partzero}{part_itt}{arguments["eseparator"]}'
            else:
                part_itt = 0
                newepnum += f'{arguments["fseparator"]}S{seasonzero}{season_nb}E{zero}{episode_itt}{arguments["eseparator"]}'

            # Print and/or act on the selected changes
            newname = filelist[m].replace(arguments["marker"], newepnum, 1)
            if "print" in arguments["options"]:
                print(f"{folderlist[n]:<25}/{filelist[m]:<50} -> {folderlist[n]:<25}/{newname:<50}")
            if not "noact" in arguments["options"]:
                os.rename(f"{parent_path}{folderlist[n]}/{filelist[m]}",f"{parent_path}{folderlist[n]}/{newname}")
            positive = True
    return positive

def replace_absolute(arguments, parent_path, episode_per_file = 1):
    ''' Changes filenames from an absolute to season based names:

    Example:
        from:
        parent_path
            Season 01
                01.mkv
                02.mkv
                ...
            Season 02
                25.mkv
                26,mkv
                ...
            ...

        to:
        parent_path
            Season 01
                S01E01.mkv
                S01E02.mkv
                ...
            Season 02
                S02E01.mkv
                S02E02.mkv
                ...
            ...

    Args:
        arguments: the options selected by the user
        parent_path: the parent path to work on
        episode_per_file: the number of episodes per file

    Returns:
        bool: Returns a positive if there was at least a match
    '''
    positive = False
    folderlist = get_content(parent_path, directories = True)
    for n in range(len(folderlist)):
        if len(re.findall('\d+', folderlist[n] )) <= 0:
            continue
        season_nb = re.findall('\d+', folderlist[n] )[0]
        episode_itt = 0
        filelist = get_content(parent_path + folderlist[n])

        # get rid of non numbered files
        filelist = [item for item in filelist if len(re.findall('\d+', item))>0]
        
        # order the list by the fist number found in the name
        filelist.sort(key=lambda item: int(re.findall('\d+', item )[0]))

        for m in range(len(filelist)):
            oldepnum = re.findall('\d+', filelist[m] )[0]
            newepnum = ""
            for i in range(episode_per_file):
                episode_itt += 1

                # Select number of zeros in season number
                seasonzero = ""
                zero = ""
                if int(season_nb) < 10 and season_nb[0] != "0":
                    seasonzero = "0"
                
                if len(filelist) >= 100 and episode_itt < 10:
                    zero = "00"
                elif len(filelist) >= 100 and episode_itt < 100:
                    zero = "0"
                elif episode_itt < 10:
                    zero = "0"
                
                # If selected replace the episode number
                if "keepep" in arguments["options"]:
                    newepnum += f'{arguments["fseparator"]}S{seasonzero}{season_nb}E{oldepnum}'
                else:
                    newepnum += f'{arguments["fseparator"]}S{seasonzero}{season_nb}E{zero}{episode_itt}'
                if i < episode_per_file:
                    newepnum += arguments["eseparator"]
                newname = filelist[m].replace(oldepnum, newepnum, 1)
                positive = True
            if "print" in arguments["options"]:
                print(f"{folderlist[n]:<25}/{filelist[m]:<45} -> {folderlist[n]:<25}/{newname:<45}")
            if not "noact" in arguments["options"]:
                os.rename(f"{parent_path}{folderlist[n]}/{filelist[m]}",f"{parent_path}{folderlist[n]}/{newname}")
    return positive

def main():
    ''' Controls the tasks

    Args:

    Returns:
    '''
    arguments = load_arguments()
    if len(arguments["paths"]) > 0:
        for path in arguments["paths"]:
            if "preserve" in arguments["options"]:
                add_numbering(arguments = arguments, parent_path = path)
            elif "doubleep" not in arguments["options"]:
                replace_absolute(arguments = arguments, parent_path = path)
            else:
                replace_absolute(arguments = arguments, parent_path = path, episode_per_file = 2)
                

if __name__ == '__main__':
    main()

