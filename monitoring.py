from subprocess import check_output
import json
import re
import os, sys
import subprocess
import psutil
import time
import socket
from pymongo import MongoClient
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM
AF_INET6 = getattr(socket, 'AF_INET6', object())
from psutil import *

class Cls_Get_Current_Process:
    def __init__(self):
        self.taskArray = []
        self.processArray = []
        self.afterTaskArray = []
        self.command = ""
        self.protoCol_Map    = {(AF_INET, SOCK_STREAM) : 'tcp',
                                (AF_INET6, SOCK_STREAM): 'tcp6',
                                (AF_INET, SOCK_DGRAM)  : 'udp',
                                (AF_INET6, SOCK_DGRAM) : 'udp6',}
         
        self.processResult = {
            "processID" : "",
            "processName" : "",
            "processStatus" : "",
            "processExePath" : "",
            "processWorkPath" : ""
        }
        self.networkResult = {
            "processID" : "",
            "processName" : "",
            "fileDescriptor" : "",
            "family" : "",
            "localAddress" : "",
            "localPort" : "",
            "remoteAddress" : "",
            "remotePort" : "",
            "status" : "",
            "ipReputation" : ""
        }
        self.processMonitoringArray = []
        self.processResultArray = []
        self.networkResultArray = []
        self.client = MongoClient('mongodb://192.168.175.154:27017/')
        self.db_conn = self.client.DB
        self.dbResult = ""
    def fnc_GetCurrentProcess(self):
        taskList = subprocess.check_output(['tasklist']).split("\r\n")
        self.taskArray = []
        for task in taskList:
            m = re.match("(.+?) +(\d+) (.+?) +(\d+) +(\d+.* K).*",task)
            if m is not None:
                self.taskArray.append({"image":m.group(1), "pid":m.group(2), "session_name":m.group(3), "session_num":m.group(4), "mem_usage":m.group(5)})

        jsonProcess = json.dumps(self.taskArray)
        jsonProcess = json.loads(jsonProcess)
        return jsonProcess


    def fnc_CurrentSate(self):
        taskData = _inh.fnc_GetCurrentProcess()
        self.processArray = []
        for data in taskData:
            self.processArray.append(data['pid']) 
        return self.processArray
            

    def fnc_RunFile(self,file_path):
        self.command = subprocess.Popen(file_path, stdout=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
        self.command.stdout
        
        
    def fnc_AfterState(self):
        afterTaskArray = _inh.fnc_GetCurrentProcess()
        self.afterTaskArray = []
        a= 0
        
        for data in afterTaskArray:
            if self.processArray.__contains__(data['pid']):
                continue
            else:
                self.afterTaskArray.append(data['pid'])
            a+=1

        return self.afterTaskArray


    def fnc_ProcessMonitoring(self):
        
        t_end = time.time() + 20 * 1
        while time.time() < t_end: # sure kadar calis
            
            monitoringArray = _inh.fnc_AfterState()
            newArray = []
            for i in monitoringArray:
                newArray.append(int(i))

            packet = psutil.net_connections()
            for data in packet:
                if newArray.__contains__(int(data.__getattribute__('pid'))):
                    if pid_exists(data.__getattribute__('pid')):
                        try:
                            process = Process(data.__getattribute__('pid'))

                            self.networkResult["processID"] = str(data.__getattribute__('pid'))
                            self.networkResult["processName"] =  str(process.name())
                            self.networkResult["fileDescriptor"] = str(data.__getattribute__('fd'))
                            self.networkResult["family"] = str(self.protoCol_Map[data.__getattribute__('family'),data.__getattribute__('type')])
                            self.networkResult["localAddress"] = str(data.__getattribute__('laddr')[0])
                            self.networkResult["localPort"] = str(data.__getattribute__('laddr')[1])
                            if data.__getattribute__('raddr'):
                                self.networkResult["remoteAddress"] = str( data.__getattribute__('raddr')[0])
                                self.networkResult["remotePort"] = str(data.__getattribute__('raddr')[1])
                                self.networkResult["status"] = str(data.__getattribute__('status'))
                            
                            self.dbResult = list(self.db_conn.blacklistcolls.find({"badIP" :  str(self.networkResult["remoteAddress"])}))
                            if self.dbResult.__len__() == 0:
                                self.networkResult["ipReputation"] = str("Trust")
                            else:
                                for record in self.dbResult:
                                    self.networkResult["ipReputation"] = str("url : " + record['url'] + "- update date : " + record["ip_update_date"])

                            self.networkResultArray.append(json.dumps(self.networkResult))
                            
                            
                            # ayni kayittan tekrar eklenmesi engellenmeli
                            # if self.networkResultArray.__len__() == 0:
                            #     self.networkResultArray.append(self.networkResult["processID"])
                            # else:
                            #     print self.networkResult
                            #     for prc in self.networkResultArray:
                            #         print "prc",prc
                            #         print "pid",self.networkResult["processID"]
                            #         if int(prc) == int(self.networkResult["processID"]):
                            #             pass
                            #         else:
                            #             self.networkResultArray.append(self.result)

                        except AccessDenied:
                            pass

 
        myProcessStr = ""
        #print newArray.__len__()
        if newArray.__len__() < 2 :
            myProcessStr = str('{"processID":"","processName":"","processStatus":"","processExePath":"","processWorkPath":""}#')
        else:
            for i in newArray:
                try:
                    process = Process(i)
                    self.processResult["processID"] = i
                    self.processResult["processName"] = process.name()
                    self.processResult["processStatus"] = process.status()
                    self.processResult["processExePath"] = process.exe()
                    self.processResult["processWorkPath"] = process.cwd()
                    self.processResultArray.append(json.dumps(self.processResult))

                    
                    myProcessStr += str(json.dumps(self.processResult)) + "#"
                except:         
                    pass 
           
        myProcessStr = myProcessStr[:-1]
        myProcessStr += '$'

        myNetworkStr = ""
        if self.networkResultArray.__len__() == 0:
            myNetworkStr += str('{"processID":"","processName":"","fileDescriptor":"","family":"","localAddress":"","localPort":"","remoteAddress":"","remotePort":"","status":"","ipReputation":""}#')
        else:
            for i in self.networkResultArray:
                try:
                    myNetworkStr += str(i) + "#"
                except:
                    pass
        myNetworkStr = myNetworkStr[:-1]

        myResult = ""
        myResult = myProcessStr + myNetworkStr
        print myResult
        self.command.terminate()             
        


if __name__ == '__main__':
    file_path = sys.argv[1]
    _inh = Cls_Get_Current_Process()
    _inh.fnc_CurrentSate()
    _inh.fnc_RunFile(file_path)
    _inh.fnc_ProcessMonitoring()
    

    
