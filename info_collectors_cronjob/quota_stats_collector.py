#!/usr/bin/env python

import os
import logging
import logging.handlers
import argparse
import json
from irods.session import iRODSSession
from irods.models import Collection, DataObject, User
from irods.column import Like, Between

logger = logging.getLogger('QuotaStatsCollector')

class Stats():


    def __init__(self):

        self.data = {'collections':{}, 'groups':{}}
        env_file = os.path.expanduser('~/.irods/irods_environment.json')
        with iRODSSession(irods_env_file=env_file) as self.session:
            self.rootCollPath = '/' + self.session.zone

            self.groups = {}
            for result in self.session.query(User).filter(User.type == 'rodsgroup').get_results():
                self.groups[result[User.name]] = self.session.user_groups.get(result[User.name])
                member_names = [user.name for user in self.groups[result[User.name]].members]
                self.data['groups'][result[User.name]] = member_names

            self.users = []
            for result in self.session.query(User).filter(User.type == 'rodsuser').get_results():
                self.users.append((result[User.name],result[User.zone]))


    def getCollectionInfo(self, path):

        results = self.session.query().count(DataObject.id).sum(DataObject.size).filter(
                               Like(Collection.name, path + '/%') or Collection.name == path).all()
        for result in results:
            self.data['collections'][path] = {'objects': result[DataObject.id],
                                              'size': result[DataObject.size],
                                              'groups': {},
                                              'users': {}
                                             }
 
        for group_name in self.groups:
            group_results = self.session.query().count(
                                    DataObject.id).sum(DataObject.size).filter(
                                    Like(Collection.name, path + '/%') or Collection.name == path).filter(
                                    DataObject.owner_name == group_name).all()
            for group_result in group_results:
                self.data['collections'][path]['groups'][group_name] = {
                                                  'objects': group_result[DataObject.id],
                                                  'size': group_result[DataObject.size]
                                                 }

        for (user_name, user_zone) in self.users:
            user_results = self.session.query().count(
                                   DataObject.id).sum(DataObject.size).filter(
                                   Like(Collection.name, path + '/%') or Collection.name == path).filter(
                                   DataObject.owner_name == user_name, DataObject.owner_zone == user_zone).all()
            for user_result in user_results:
                self.data['collections'][path]['users'][user_name] = {
                                                  'objects': user_result[DataObject.id],
                                                  'size': user_result[DataObject.size]
                                                 }


    def getCollectionsInfo(self, path, maxLevel):

        self.getCollectionInfo(path)
        coll = self.session.collections.get(path)
        if len(path.split('/')) <= maxLevel:
            for col in coll.subcollections:
                self.getCollectionsInfo(col.path, maxLevel)


    def getRoot(self):
        return self.rootCollPath

    def getSession(self):
        return self.session

    def getData(self):
        return self.data


def _initializeLogger(args):
    """initialize the logger instance."""

    if (args.debug):
        logger.setLevel(logging.DEBUG)
    if (args.log):
        han = logging.handlers.RotatingFileHandler(args.log,
                                                   maxBytes=6000000,
                                                   backupCount=9)
        formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        han.setFormatter(formatter)
        logger.addHandler(han)


def computeStats(args):
    """compute the statistics."""

    statistics = Stats()
    collPath = statistics.getRoot()
    maxLevel = 2
    statistics.getCollectionsInfo(collPath, maxLevel)
    print json.dumps(statistics.getData())


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='EUDAT quota stats client')

    parser.add_argument("-l", "--log", help="Path to the log file")
    parser.add_argument("-d", "--debug", help="Show debug output",
                        action="store_true")
    parser.add_argument("-pl", "--pathList",
                        help='the path to the file containing the directories'
                           + ' whose statistics need to be computed')
    parser.add_argument("-mk", "--metaKeys", nargs='+', 
                        help='the metadata keys to extract')
    parser.set_defaults(func=computeStats)

    _args = parser.parse_args()
    _initializeLogger(_args)
    _args.func(_args)

# print first level: root zone dir
# size
# 	total, per user, per group + dynamic attributes
# number of objects
#       total, per user, per group + dynamic attributes
# print second level: 
# size
#       total, per user, per group + dynamic attributes
# number of objects
#       total, per user, per group + dynamic attributes
# print third level: 
# size
#       total, per user, per group + dynamic attributes
# number of objects
#       total, per user, per group + dynamic attributes
# print custom paths read from input
# size
#       total, per user, per group + dynamic attributes
# number of objects
#       total, per user, per group + dynamic attributes
# 

