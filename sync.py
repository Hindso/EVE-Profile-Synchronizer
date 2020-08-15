from pathlib import Path,PurePath
import argparse
import time
import os
import sys

parser = argparse.ArgumentParser(description="Synchronize the settings between all of your EVE characters and accounts")

parser.add_argument("--char", action="store", dest="char_id", help="the identifier of the source character, used in core_char .dat files")
parser.add_argument("--acc", action="store", dest="acc_id", help="the identifier of the source account, used in core_user .dat files")
parser.add_argument("--dir", action="store", dest="dir", help="the directory containing the core .dat files")

args = parser.parse_args()

# Find the settings directory
if args.dir is not None:
    sourceDir = args.dir
else:
    # Guess the directory
    localAppData = os.getenv('LOCALAPPDATA')
    defaultPartialPath = localAppData+'\\CCP\\EVE'
    try:
        for folder in Path(defaultPartialPath).iterdir():
            if 'tq_tranquility' in folder.name:
                defaultPath = folder
                break
    except:
        print('Bad guess at settings directory. Please inform the developer')

    print("The following directory has been detected, is this the correct path for your EVE settings? (y/n)\n", defaultPath)
    if input() == "y":
        folders = []
        for folder in Path(defaultPath).iterdir():
            if folder.is_dir():
                if "settings" in folder.name:
                    folders.append(folder)

        if len(folders) == 0:
            print("No settings profile detected, please make one")
        elif len(folders) == 1:
            sourceDir = folder
        elif len(folders) > 1:
            print("Multiple profiles detected, please select one:")
            for index, folder in enumerate(folders):
                print(str(index)+')', folder.name)
            x = input()
            try:
                sourceDir = folders[int(x)]
                print("Using", folders[int(x)])
            except:
                print("Invalid directory")
                sys.exit()
    else:
        sourceDir = input('Then please provide the correct directory: ')


# Check the directory is functional and has settings files in it
found = False

try:
    p = Path(sourceDir)
    for item in p.iterdir():
        if item.is_file():
            if item.match("*core_char_[0-9]*"):
                found = True
                break
except:
    print('Invalid directory')
    sys.exit()

if found == False:
    print("Could not find settings files in directory")
    sys.exit()


# Sort out the name of the source file, or determine to use the last modified files as the source
if args.char_id is None or args.acc_id is None:
    if args.char_id is None:
        print('You did not provide a source user settings file')
    else:
        char_sourcename = 'core_char_'+args.char_id
    if args.acc_id is None:
        print('You did not provide a source account settings file')
    else:
        acc_sourcename = 'core_user_'+args.acc_id

    useLastModified = input('Use last modified settings file as source (y/n)? ') == "y"

    if useLastModified == True:
        input('Ensure that the character/account you want to copy the settings from was the last to log out\nBackups will be made of your old settings files\nPress enter to continue...')

    if useLastModified == False:
        if args.char_id is None:
            char_sourcename = input('Then please provide your source character settings file: ')
        if args.acc_id is None:
            acc_sourcename = input('Then please provide your source account settings file: ')
    else:
        char_sourcename = None
        acc_sourcename = None
else:
    char_sourcename = 'core_char_'+args.char_id
    acc_sourcename = 'core_user_'+args.acc_id

currentCharLastModified = 0
currentAccLastModified = 0
characters = []
accounts = []

# Iterate over directory - collate all the character/account settings files, find the file to use as the source of the sync
for item in p.iterdir():
    if item.is_file():
        if item.match("*core_char_[0-9]*"):
            characters.append(item)
            if char_sourcename is not None and char_sourcename in item.name:
                char_source_file = item
            elif char_sourcename is None and useLastModified == True:
                lastModified = os.path.getmtime(item)
                if lastModified > currentCharLastModified:
                    char_source_file = item
                    currentCharLastModified = lastModified
        elif item.match("*core_user_[0-9]*"):
            accounts.append(item)
            if acc_sourcename is not None and acc_sourcename in item.name:
                acc_source_file = item
            if acc_sourcename is None and useLastModified == True:
                lastModified = os.path.getmtime(item)
                if lastModified > currentAccLastModified:
                    acc_source_file = item
                    currentAccLastModified = lastModified

# Make backup directory
backupdir_name = 'backup ' + time.strftime("%Y-%m-%d %H-%M-%S")
backupdir = Path(str(sourceDir) + '\\' + backupdir_name)
backupdir.mkdir(exist_ok=True)
try:
    print("Character source file: " + char_source_file.name)
    char_source = char_source_file.open("rb").read()
except:
    print("Could not open character source file")
    sys.exit()
try:
    print("Account source file: " + acc_source_file.name)
    acc_source = acc_source_file.open("rb").read()
except:
    print("Could not open account source file")
    sys.exit()

# Move current files to backup directory
try:
    for item in characters+accounts:
        item.replace(str(backupdir) + "\\" + item.name)
    print("Backups created in \'"+backupdir_name+"\'")
except:
    print("Error backing up settings")

# Create new character files
try:
    for item in characters:
        item.open("wb").write(char_source)
except:
    print("Error syncing character settings")

# Create new account files
try:
    for item in accounts:
        item.open("wb").write(acc_source)
except:
    print("Error syncing account settings")

input('Press Enter to exit')
sys.exit()