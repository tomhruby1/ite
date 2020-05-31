import paho.mqtt.client as mqtt
import requests
from json import dumps as dumps_json, loads as loads_json
import re
from tinydb import TinyDB, Query
import websockets
import asyncio
import datetime
import tornado.websocket
from websocket import WebSocketApp


db = TinyDB('Temp.json')
Hour_avg=TinyDB('Hour_avg.json')
StatsDB=TinyDB('StatsDB.json')

global Teams_List
Teams_List=['green','black','pink','yellow','blue','orange','red']

class DayStats:
    """Trida pro ulozeni a praci s dennimi statistikami"""
    max=[float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf')]
    min =[float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf')]
    avg=[0,0,0,0,0,0,0]
    count=[0,0,0,0,0,0,0]
    sum = [0,0,0,0,0,0,0]
    day=datetime.datetime.now().day
    def midnight(self):
        StatsDB.insert({"day_stats.avg": self.avg,"day_stats.max":self.max,"day_stats.min":self.min})
        self.max=[float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf')]
        self.min=[float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf')]
        self.sum=[0,0,0,0,0,0,0]
        self.count=[0,0,0,0,0,0,0]
        self.day=datetime.datetime.now().day
    
class HourStats:
    """Trida pro ulozeni a praci s dennimi statistikami"""
    max=[float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf')]
    min =[float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf')]
    avg=[0,0,0,0,0,0,0]
    count=[0,0,0,0,0,0,0]
    sum = [0,0,0,0,0,0,0]
    hour=datetime.datetime.now().hour
    def fullhour(self):
        self.hour=datetime.datetime.now().hour
        hour_Str=str(self.hour)
        hour_Str=hour_Str+':00'
        for teamname in Teams_List:
            index_stats=teams_dict[teamname]
            Hour_avg.insert({'team': teamname, 'time':  hour_Str, 'temperature': self.avg[index_stats]})
        self.max=[float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf')]
        self.min=[float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf')]
        self.sum=[0,0,0,0,0,0,0]
        self.count=[0,0,0,0,0,0,0]






global New_data
New_data=[0,0,0,0,0,0,0]
SERVER = '147.228.124.230'  # RPi
TOPIC = 'ite/#'
global Data_to_be_send
global offline_data
period=1
global alert
alert=False
teams_send_dict={'green':1,'black':2,'pink': 3,'yellow' : 4,'blue' : 5,'orange' : 6,'red' : 7}
teams_dict={'green':1,'black':0,'pink': 2,'yellow' : 3,'blue' : 4,'orange' : 5,'red' : 6,'1' : 'green','0' : 'black','2' : 'pink',
               '3' : 'yellow','4' : 'blue','5' : 'orange','6' : 'red'}
url_base = 'https://uvb1bb4153.execute-api.eu-central-1.amazonaws.com/Prod'

global day_stats
day_stats=DayStats()
global hour_Stats
hour_stats=HourStats()



headers_base = {'Content-Type': 'application/json'}
url_post=url_base+'/measurements'
headers_post = dict(headers_base)
sensor_UUID=''
Data_to_be_send=[0,0,0,0,0,0,0]
offline_data=[0,0,0,0,0,0,0]

def login():
    """Metoda vraci UUID tymu, a zaroven updatuje headers o dane teamUUID"""

    url_login = url_base+'/login'
    body_login = {'username': 'Green', 'password': '}Xe6BL^k'}
    # login
    login_data = loads_json(requests.post(url_login, data=dumps_json(body_login), headers=headers_base).text)
    print('\nLogin data:', login_data)

    teamUUID = login_data['teamUUID']
    print('\nteamUUID:', teamUUID)
    headers_post.update({'teamUUID': teamUUID})

    return(teamUUID)

def getsensor():
    """Metoda vraci list ve kterem je sensorUUID,maximalni teplota a minimalni teplota"""

    url_sensor = url_base+'/sensors'
    sensor_data= str(loads_json(requests.get(url_sensor, headers=headers_post).text))
    sensor_UUID=re.search('(?<=\'sensorUUID\': \').+?(?=\',)',sensor_data,re.DOTALL).group().strip() #vyhledani sensor UUID ve stringu
    minimum=re.search('(?<=\'minTemperature\': ).+(?=,)',sensor_data,re.DOTALL).group().strip()    #vyhledani minimalni tepltoy ve stringu
    maximum=re.search('(?<=\'maxTemperature\': ).+(?=})',sensor_data,re.DOTALL).group().strip() #vyhledani maximalni UUID ve stringu
    minimum=float(minimum)
    maximum=float(maximum)
    sensor_UUID=str(sensor_UUID)          
    return(sensor_UUID,maximum,minimum)          

def on_connect(client, userdata, mid, qos):
    print('Connected with result code qos:', str(qos))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    now = datetime.datetime.now()
    if (msg.payload == 'Q'):
        client.disconnect()
    data=str(msg.payload)
    team_name=re.search('(?<="team_name": ").+?(?=",)',data,re.DOTALL).group().strip()
    team_name=str(team_name)
    created_on=re.search('(?<="created_on": ").+?(?=", "temperature")',data,re.DOTALL).group().strip()
    temperature=re.search('(?<="temperature": ).+?(?=})',data,re.DOTALL).group().strip()
    data={"createdOn": created_on[:-3]+"+01:00","sensorUUID": sensor_UUID, "temperature": temperature, 'status': 'TEST'}
    temperature_float=float(temperature)
    global New_data
    global alert
    global hour_stats
    global offline_data
    global day_stats
    status="online"
    if team_name=="green":
        b=requests.post(url_post,data=dumps_json(data),headers=headers_post)
        if ((temperature_float<minimum or temperature_float>maximum) and alert==False) :
            dataalert={"createdOn": created_on[:-3]+"+01:00","sensorUUID": sensor_UUID, "temperature": temperature, "lowTemperature": minimum, "highTemperature": maximum}
            url_alert=url_base+'/alerts'
            b=requests.post(url_alert,data=dumps_json(dataalert),headers=headers_post)
            alert=True
        if (temperature_float>minimum and temperature_float<maximum and alert):
            alert=False
        if alert==True:
            status="alert"    
    #Vypocet statistickych dat
    if day_stats.day != datetime.datetime.now().day:          #pulnoc nulovani statistik
        day_stats.midnight()
        
    

    index_stats=teams_dict[team_name]

    if float(day_stats.min[index_stats])>temperature_float:
        day_stats.min[index_stats]=str(round(temperature_float,3))

    if float(day_stats.max[index_stats])<temperature_float:
        day_stats.max[index_stats]=str(round(temperature_float,3))

    day_stats.sum[index_stats]=day_stats.sum[index_stats]+temperature_float
    hour_stats.sum[index_stats]=hour_stats.sum[index_stats]+temperature_float
    day_stats.count[index_stats]=day_stats.count[index_stats]+1
    hour_stats.count[index_stats]=hour_stats.count[index_stats]+1
    day_stats.avg[index_stats]=str(round(day_stats.sum[index_stats]/day_stats.count[index_stats],3))
    hour_stats.avg[index_stats]=hour_stats.sum[index_stats]/hour_stats.count[index_stats]
    db.insert({'team': team_name, 'time':  created_on, 'temperature': temperature})
    load_data=Load_last_data_from_DB(team_name,status,day_stats.avg[index_stats],day_stats.min[index_stats],day_stats.max[index_stats])
    Data_to_be_send[int(teams_dict[team_name])]=load_data[0]
    offline_data[int(teams_dict[team_name])]=load_data[1]

    if hour_stats.hour!=datetime.datetime.now().hour:
        hour_stats.fullhour()
    New_data[teams_dict[team_name]]=1



def Load_last_data_from_DB(teamname,status,day_avg,minimum,maximum):
    teamQuery = Query()
    send=[0,0]
    ID=teams_send_dict[teamname]
    last_data=[]
    time=[]
    for i in range(-10,0):
        last_data.append(db.search(teamQuery.team == teamname)[i]['temperature'][:-11])
        time.append(db.search(teamQuery.team == teamname)[i]['time'][11:-7])  
    slovnik_k_odeslani={"id":ID,"status":status,"data":last_data,"times":time,"max":maximum,"min":minimum,"avg":day_avg}
    slovnik_k_odeslani=dumps_json(slovnik_k_odeslani)
    slovnik_offline={"id":ID,"status":'offline',"data":last_data,"times":time,"max":maximum,"min":minimum,"avg":day_avg}
    slovnik_offline=dumps_json(slovnik_offline)
    send[0]=slovnik_k_odeslani
    send[1]=slovnik_offline
    
    return(send)

async def Client_loop(websocket, path):
    i=0
    for i in Data_to_be_send:
        await websocket.send(str(i))
        await asyncio.sleep(0.1)
    teams=[0,0,0,0,0,0,0]
    while True:
        if max(New_data)==1:
            indexnovadata=str(New_data.index(max(New_data)))
            team=teams_dict[indexnovadata]
            await websocket.send(Data_to_be_send[int(indexnovadata)])
            await asyncio.sleep(period)
            New_data[int(indexnovadata)]=0
            i=0
            teams[int(indexnovadata)]=0
        
        if(max(teams)>80):
            if offline_data[int(teams.index(max(teams)))]!=0:
                await websocket.send(offline_data[int(teams.index(max(teams)))])
                await asyncio.sleep(period)

            teams[teams.index(max(teams))]=0
        
        for i in range(len(teams)):
            teams[i] += period
        
        await asyncio.sleep(period)
         





    
    
def main():
    teamUUID=login()
    data=getsensor()
    global sensor_UUID
    global minimum
    global maximum
    minimum=float(data[2])
    maximum=float(data[1])
    sensor_UUID=data[0]
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set('mqtt_student', password='pivo')

    client.connect(SERVER, 1883, 60)
    
    start_server = websockets.serve(Client_loop, "147.228.121.46", 8882)   #147.228.121.46
    client.loop_start()
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    



if __name__ == '__main__':
    main()
