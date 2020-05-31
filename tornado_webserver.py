#!/usr/env/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from tornado.web import StaticFileHandler, Application as TornadoApplication
from tornado.ioloop import IOLoop
from os.path import dirname, join as join_path
import tornado.gen
import json
from tinydb import TinyDB, Query
from datetime import date, timedelta

# last 24 hours data for each team(for chart0)
def histFromDb():
        db = TinyDB('Hour_avg.json')
        name2id ={'green':1,'black':2,'pink': 3,'yellow' : 4,'blue' : 5,'orange' : 6,'red' : 7}
        structData = {1:{"data":[], "time":[]}, 2:{"data":[], "time":[]}, 3:{"data":[], "time":[]}, 4:{"data":[], "time":[]}, 5:{"data":[], "time":[]}, 6:{"data":[], "time":[]}, 7:{"data":[], "time":[]}, "statistics":{}}

        #get 24 hrs history from db of given team
        def teamHistory(teamName):
            data = []
            time = []
            teamQuery = Query()
            for i in range(-24, 0):
                data.append(db.search(teamQuery.team == teamName)[i]['temperature'])
                time.append(db.search(teamQuery.team == teamName)[i]['time'])

            return data, time

        teamNames = ["red", "green", "blue", "orange", "pink", "black", "yellow"]
        for teamName in teamNames:
            teamData, teamTime = teamHistory(teamName)
            teamid = name2id[teamName]
            structData[teamid]["data"] = teamData
            structData[teamid]["time"] = teamTime

        return json.dumps(structData)


#Last 3 days statistics from db for each team
def histStatsFromDb():
    from tinydb import TinyDB, Query
    db=TinyDB('StatsDB.json')
    Query = Query()

    #getting days from date for statistics data
    d1 = (date.today() - timedelta(days=1)).strftime('%a')
    d2 = (date.today() - timedelta(days=2)).strftime('%a')
    d3 = (date.today() - timedelta(days=3)).strftime('%a')

    data = {"avg":[], "min":[], "max":[], "days":[d3,d2,d1]}
    d0 = ['Black','Green','Pink','Yellow','Blue','Orange','Red']
    d1 = db.search(Query)[-1]
    d2 = db.search(Query)[-2]
    d3 = db.search(Query)[-3]

    #tuples of 3 values per day for each team
    data["avg"] = list(zip(d3["denni_prumer"], d2["denni_prumer"], d1["denni_prumer"]))
    data["min"] = list(zip(d3["denni_minimum"], d2["denni_minimum"], d1["denni_minimum"]))
    data["max"] = list(zip(d3["denni_maximum"], d2["denni_maximum"], d1["denni_maximum"]))
    data["head"] = d0

    return data

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        data_str = histFromDb()
        stats_str = histStatsFromDb()
        self.render('./templates/index.html', data=data_str, stats=stats_str)


if __name__ == '__main__':
    app = TornadoApplication([
        (r'/', MainHandler),
        (r'/(.*)', StaticFileHandler, {
            'path': join_path(dirname(__file__), 'assets')}),
    ])

    # Port
    TORNADO_PORT = 8881
    app.listen(TORNADO_PORT)

    # Start the server
    tornado.ioloop.IOLoop.current().start()
