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
stary_data=TinyDB('historie.json')
statistika=TinyDB('statistika.json')
global novadata
novadata=[0,0,0,0,0,0,0]
SERVER = '147.228.124.230'  # RPi
TOPIC = 'ite/#'
global datakodeslani
global offline_data
perioda=1
global alert
alert=False
teams_slovnik_odeslani={'green':1,'black':2,'pink': 3,'yellow' : 4,'blue' : 5,'orange' : 6,'red' : 7}
teams_slovnik={'green':1,'black':0,'pink': 2,'yellow' : 3,'blue' : 4,'orange' : 5,'red' : 6,'1' : 'green','0' : 'black','2' : 'pink',
               '3' : 'yellow','4' : 'blue','5' : 'orange','6' : 'red'}
url_base = 'https://uvb1bb4153.execute-api.eu-central-1.amazonaws.com/Prod'
global seznam_tymu
seznam_tymu=['green','black','pink','yellow','blue','orange','red']

global denni_maximum
denni_maximum=[float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf')]
global denni_minimum
denni_minimum=[float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf')]
global denni_suma
denni_suma=[0,0,0,0,0,0,0]
global denni_pocet
denni_pocet=[0,0,0,0,0,0,0]
global day
day=datetime.datetime.now().day
global hour
hour=datetime.datetime.now().hour
global denni_prumer
denni_prumer=[0,0,0,0,0,0,0]
global hour_avg
hour_avg=[0,0,0,0,0,0,0]
global hour_sum
hour_sum=[0,0,0,0,0,0,0]
global hour_counter
hour_counter=[0,0,0,0,0,0,0]


headers_base = {'Content-Type': 'application/json'}
url_post=url_base+'/measurements'
headers_post = dict(headers_base)
sensor_UUID=''
datakodeslani=[0,0,0,0,0,0,0]
offline_data=[0,0,0,0,0,0,0]

def login():   #metoda vraci UUID tymu, a zaroven updatuje headers o dane teamUUID
    url_login = url_base+'/login'
    body_login = {'username': 'Green', 'password': '}Xe6BL^k'}
# login
    login_data = loads_json(requests.post(url_login, data=dumps_json(body_login), headers=headers_base).text)
    print('\nLogin data:', login_data)

    teamUUID = login_data['teamUUID']
    print('\nteamUUID:', teamUUID)
    headers_post.update({'teamUUID': teamUUID})

    return(teamUUID)

def getsensor(): #metoda vraci list ve kterem je sensorUUID,maximalni teplota a minimalni teplota
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
    a=str(msg.payload)
    data=a
    team_name=re.search('(?<="team_name": ").+?(?=",)',data,re.DOTALL).group().strip()
    team_name=str(team_name)
    created_on=re.search('(?<="created_on": ").+?(?=", "temperature")',data,re.DOTALL).group().strip()
    temperature=re.search('(?<="temperature": ).+?(?=})',data,re.DOTALL).group().strip()
    data={"createdOn": created_on[:-3]+"+01:00","sensorUUID": sensor_UUID, "temperature": temperature, 'status': 'TEST'}
    teplota=float(temperature)
    global denni_minimum
    global denni_maximum   
    global denni_suma
    global novadata
    global alert
    global day
    global denni_prumer
    global denni_pocet
    global hour_avg
    global hour_sum
    global hour_counter
    global hour
    global offline_data
    status="online"
    if team_name=="green":
        b=requests.post(url_post,data=dumps_json(data),headers=headers_post)
        if ((teplota<minimum or teplota>maximum) and alert==False) :
            dataalert={"createdOn": created_on[:-3]+"+01:00","sensorUUID": sensor_UUID, "temperature": temperature, "lowTemperature": minimum, "highTemperature": maximum}
            url_alert=url_base+'/alerts'
            b=requests.post(url_alert,data=dumps_json(dataalert),headers=headers_post)
            alert=True
        if (teplota>minimum and teplota<maximum and alert):
            alert=False
        if alert==True:
            status="alert"    
    #tady delame statistiky 
    if day != datetime.datetime.now().day:          #pulnoc nulovani statistik
        statistika.insert({"denni_prumer": denni_prumer,"denni_maximum":denni_maximum,"denni_minimum":denni_minimum,})
        denni_maximum=[float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf'),float('-inf')]
        denni_minimum=[float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf'),float('inf')]
        denni_suma=[0,0,0,0,0,0,0]
        denni_pocet=[0,0,0,0,0,0,0]
        day=datetime.datetime.now().day
    index_statistika=teams_slovnik[team_name]
    if float(denni_minimum[index_statistika])>teplota:
        denni_minimum[index_statistika]=str(round(teplota,3))
    if float(denni_maximum[index_statistika])<teplota:
        denni_maximum[index_statistika]=str(round(teplota,3))
    denni_suma[index_statistika]=denni_suma[index_statistika]+teplota
    hour_sum[index_statistika]=hour_sum[index_statistika]+teplota
    denni_pocet[index_statistika]=denni_pocet[index_statistika]+1
    hour_counter[index_statistika]=hour_counter[index_statistika]+1
    denni_prumer[index_statistika]=str(round(denni_suma[index_statistika]/denni_pocet[index_statistika],3))
    hour_avg[index_statistika]=hour_sum[index_statistika]/hour_counter[index_statistika]
    db.insert({'team': team_name, 'time':  created_on, 'temperature': temperature})
    nactena_data=nactidata(team_name,status,denni_prumer[index_statistika],denni_minimum[index_statistika],denni_maximum[index_statistika])
    datakodeslani[int(teams_slovnik[team_name])]=nactena_data[0]
    offline_data[int(teams_slovnik[team_name])]=nactena_data[1]
    if hour!=datetime.datetime.now().hour:
        hour=datetime.datetime.now().hour
        hour_Str=str(hour)
        hour_Str=hour_Str+':00'
        for teamname in seznam_tymu:
            index_statistika=teams_slovnik[teamname]
            stary_data.insert({'team': teamname, 'time':  hour_Str, 'temperature': hour_avg[index_statistika]})
        hour_avg=[0,0,0,0,0,0,0]
        hour_sum=[0,0,0,0,0,0,0]
        hour_counter=[0,0,0,0,0,0,0]
    novadata[teams_slovnik[team_name]]=1


#def historiedat():
#    teamQuery = Query()
#    for teamname in seznam_tymu:
#        temperature=db.search(teamQuery.team == teamname)[-1]['temperature'][:-11]
#        created_on=db.search(teamQuery.team == teamname)[-1]['time'][11:-7]
#        stary_data.insert({'team': teamname, 'time':  created_on, 'temperature': temperature})




def nactidata(teamname,status,denni_prumer,minimum,maximum):
    teamQuery = Query()
    send=[0,0]
    ID=teams_slovnik_odeslani[teamname]
    hodnoty=[]
    time=[]
    for i in range(-10,0):
        hodnoty.append(db.search(teamQuery.team == teamname)[i]['temperature'][:-11])
        time.append(db.search(teamQuery.team == teamname)[i]['time'][11:-7])  
    slovnik_k_odeslani={"id":ID,"status":status,"data":hodnoty,"times":time,"max":maximum,"min":minimum,"avg":denni_prumer}
    slovnik_k_odeslani=dumps_json(slovnik_k_odeslani)
    slovnik_offline={"id":ID,"status":'offline',"data":hodnoty,"times":time,"max":maximum,"min":minimum,"avg":denni_prumer}
    slovnik_offline=dumps_json(slovnik_offline)
    send[0]=slovnik_k_odeslani
    send[1]=slovnik_offline
    
    return(send)

async def time(websocket, path):
    i=0
    global denni_minimum
    global denni_maximum
    global denni_prumer
    for i in datakodeslani:
        await websocket.send(str(i))
        await asyncio.sleep(0.1)
    teams=[0,0,0,0,0,0,0]
    while True:
        if max(novadata)==1:
            indexnovadata=str(novadata.index(max(novadata)))
            team=teams_slovnik[indexnovadata]
            await websocket.send(datakodeslani[int(indexnovadata)])
            await asyncio.sleep(perioda)
            novadata[int(indexnovadata)]=0
            i=0
            teams[int(indexnovadata)]=0
        
        if(max(teams)>80):
            if offline_data[int(teams.index(max(teams)))]!=0:
                await websocket.send(offline_data[int(teams.index(max(teams)))])
                await asyncio.sleep(perioda)

            teams[teams.index(max(teams))]=0
        
        for i in range(len(teams)):
            teams[i] += perioda
        
        await asyncio.sleep(perioda)
         





    
    
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
   
    
    
    start_server = websockets.serve(time, "147.228.121.46", 8882)   #147.228.121.46
    client.loop_start()
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    
    

if __name__ == '__main__':
    main()
