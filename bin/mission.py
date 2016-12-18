# -*- coding:utf-8 -*-
# !~/anaconda/bin/python

"""
    Job handler module, interactive with bee to complete mission.
    Include base job handler class, and all kinds of other job handler class

    a mission should include some basic information:
    {
          'type': the mission's type
          'm_id': the mission's identification
          'o_id': the mission's objective
        'params': the mission's params, this can be different among all kind of mission.
    }
"""


class Downloader(object):
    """ The file download mission handler class """

    def __init__(self):
        pass

    def handler(self):
        pass
