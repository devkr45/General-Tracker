#!/usr/bin/env python3
from importlib.metadata import files
import json
import argparse
import sys
import threading

from GeneralTracker import GeneralItem


def worker(item: GeneralItem) -> bool:
    print(item.track())


def read_json_items(file_name: str):
    # Read the json file and turn it into dictionary
    tracker_list = None
    with open(file_name) as f:
        tracker_list = json.load(f, object_hook=GeneralItem.from_json)
    
    return tracker_list

    

def parse_args(*sys_args):
    parser = argparse.ArgumentParser(description=" Description ")
    subparser = parser.add_subparsers(dest="command")
    run = subparser.add_parser("run")
    create = subparser.add_parser("create")
    run.add_argument("-i", "--items", default="items.json", help="Json file that contains items to track", required=False)
    create.add_argument("-f", "--filename", default="items.json", help="Json file that contains items", required=False)

    # Variables to run GeneralTracker
    file_items = "items.json"

    # check the arguments
    args = parser.parse_args()
    if args.command=="run":
        if args.items:
            file_items = args.items

        #Call Function that reads the json file and calls the general tracker
        return read_json_items(file_items)

    elif args.command=="create":
        if args.filename:
            file_items = args.filename

            # Create the file in current dirctory
            try:
                open(file_items, "x")
            except:
                print("Error creating file {0}".format(file_items))
                return None

    
    

def main():
    # read the args
    tracker_list = parse_args()

    # Worker list
    worker_list = list()

    # If the retuend list is not empty
    if tracker_list is not None:
        # Loop thru the list of tracker
        for tracker in tracker_list:
            # check to see if less than or greate then is used only with number
            if tracker.valid_check() is False:
                sys.exit("Please make sure that you use less than or greater than only with numberical checks")
            # Start worker thread to watch the tracker
            #work = threading.Thread(target=worker, args=(tracker, ))
            #worker_list.append(work)
            #work.start()
            if tracker.track() is True:
                # Notify and then return\
                tracker.notification.notify(tracker.url, tracker.check, tracker.check_against)

    

if __name__ == "__main__":
    main()
