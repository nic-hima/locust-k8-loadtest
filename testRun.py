''' Current assumptions:
    --

'''
import os
import sys
import argparse
import shlex, subprocess
import datetime
import time
from  prometheus_http_client import Prometheus
from kubernetes import client, config
import json
import csv
import yaml
from clusterConfig import clusterSetup

#TODO: Add ability to place interference pods on specific nodes in cluster
#TODO: Add ability to scale different number of pods for each micro-service
#TODO: Figure out strategy for pod isolation on nodes when applying interference to those specific pod(s)
class podDataCollection(object):
    podName = ""
    cpu5s = []
    memW5s = []
    memR5s = []
    netW5s = []
    netR5s = []

    def __init__(self, name):
        self.podName = name

# TODO: move static config of this object to a conf file so it isn't hard coded    
class clusterInfo(object):
    testNS = "default"
    workflowDeplList = {"cart": 0, "shipping": 0, "catalogue": 0}
    iFerenceDepNm = ""
    interferenceZone = ""
    interferenceLvl = 0

    
def testDirInit(expName):
    workingDir = os.getcwd()
    testDirStr = os.path.join(workingDir, expName)
    if not os.path.exists(testDirStr):
        os.makedirs(testDirStr)
    return testDirStr

def moveLocustResults(testDirPath):
    workingDir = os.getcwd()
    if os.path.isfile(os.path.join(workingDir , 'locust_distribution.csv')):
        if not os.path.exists(testDirPath):
            os.makedirs(testDirPath)
        os.rename(os.path.join(workingDir, 'locust_distribution.csv'), os.path.join(testDirPath, 'locust_distribution.csv'))
    else:
        print("Unable to find locust_distribution.csv for destination folder %s\n", testDirPath)

    if os.path.isfile(os.path.join(workingDir, 'locust_requests.csv')):
        if not os.path.exists(testDirPath):
            os.makedirs(testDirPath)
        os.rename(os.path.join(workingDir, 'locust_requests.csv'), os.path.join(testDirPath , 'locust_requests.csv'))
    else:
        print("Unable to find locust_requests.csv for destination folder %s\n", testDirPath)

# generate and save container metrics csv files in testing dir
def createRawCSVs(tStampList, podNmList, testDirPath, podMetDict):
    # create CPU csv
    with open(os.path.join(testDirPath, 'container-cpu5sRaw.csv'), mode='w') as cpu_file:
        fieldnms = ['Pod_Name']
        fieldnms.extend(tStampList)
        writer = csv.DictWriter(cpu_file, fieldnames=fieldnms)
        writer.writeheader()
        
        for pod in podNmList:
            cpuVals = podMetDict[pod].cpu5s
            rowDict = {'Pod_Name' : pod }
            for pair in cpuVals:
                rowDict[pair[0]] = pair[1]
            writer.writerow(rowDict) 
    # create MemW/R csv
    with open(os.path.join(testDirPath, 'container-memR5sRaw.csv'), mode='w') as memR_file:
        fieldnms = ['Pod_Name']
        fieldnms.extend(tStampList)
        writer = csv.DictWriter(memR_file, fieldnames=fieldnms)
        writer.writeheader()
        
        for pod in podNmList:
            memRVals = podMetDict[pod].memR5s
            rowDict = {'Pod_Name' : pod }
            for pair in memRVals:
                rowDict[pair[0]] = pair[1]
            writer.writerow(rowDict)

    with open(os.path.join(testDirPath, 'container-memW5sRaw.csv'), mode='w') as memW_file:
        fieldnms = ['Pod_Name']
        fieldnms.extend(tStampList)
        writer = csv.DictWriter(memW_file, fieldnames=fieldnms)
        writer.writeheader()
        
        for pod in podNmList:
            memWVals = podMetDict[pod].memW5s
            rowDict = {'Pod_Name' : pod }
            for pair in memWVals:
                rowDict[pair[0]] = pair[1]
            writer.writerow(rowDict)

    # create NetW/R csv
    with open(os.path.join(testDirPath, 'container-netR5sRaw.csv'), mode='w') as netR_file:
        fieldnms = ['Pod_Name']
        fieldnms.extend(tStampList)
        writer = csv.DictWriter(netR_file, fieldnames=fieldnms)
        writer.writeheader()
        
        for pod in podNmList:
            netRVals = podMetDict[pod].netR5s
            rowDict = {'Pod_Name' : pod }
            for pair in netRVals:
                rowDict[pair[0]] = pair[1]
            writer.writerow(rowDict)

    with open(os.path.join(testDirPath, 'container-netW5sRaw.csv'), mode='w') as netW_file:
        fieldnms = ['Pod_Name']
        fieldnms.extend(tStampList)
        writer = csv.DictWriter(netW_file, fieldnames=fieldnms)
        writer.writeheader()
        
        for pod in podNmList:
            netWVals = podMetDict[pod].netW5s
            rowDict = {'Pod_Name' : pod }
            for pair in netWVals:
                rowDict[pair[0]] = pair[1]
            writer.writerow(rowDict)

# promQueries function 
def promQueries(startTime, stopTime, testDirPath):
    prom = Prometheus()
    
    cpu5s = json.loads(prom.query_rang(metric='sum(container_cpu_usage_seconds_total{namespace="default"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    memWriteB5s = json.loads(prom.query_rang(metric='sum(container_fs_writes_bytes_total{namespace="default"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    memReadB5s = json.loads(prom.query_rang(metric='sum(container_fs_reads_bytes_total{namespace="default"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    netReadB5s = json.loads(prom.query_rang(metric='sum(container_network_receive_bytes_total{namespace="default"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    netWriteB5s = json.loads(prom.query_rang(metric='sum(container_network_transmit_bytes_total{namespace="default"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))

    """ cpu5s = json.loads(prom.query_rang(metric='sum(container_cpu_usage_seconds_total{namespace="robot-shop"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    memWriteB5s = json.loads(prom.query_rang(metric='sum(container_fs_writes_bytes_total{namespace="robot-shop"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    memReadB5s = json.loads(prom.query_rang(metric='sum(container_fs_reads_bytes_total{namespace="robot-shop"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    netReadB5s = json.loads(prom.query_rang(metric='sum(container_network_receive_bytes_total{namespace="robot-shop"}) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    netWriteB5s = json.loads(prom.query_rang(metric='sum(container_network_transmit_bytes_total{namespace="robot-shop"}) by (pod_name)', start=startTime, end=stopTime, step='5s')) """
    
    # Can use queries below to find rate of change also
    """  cpuAvg = json.loads(prom.query_rang(metric='sum(rate(container_cpu_usage_seconds_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    memWriteBavg = json.loads(prom.query_rang(metric='sum(rate(container_fs_writes_bytes_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    memReadBavg = json.loads(prom.query_rang(metric='sum(rate(container_fs_reads_bytes_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    netReadBavg = json.loads(prom.query_rang(metric='sum(rate(container_network_receive_bytes_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s'))
    netWriteBavg = json.loads(prom.query_rang(metric='sum(rate(container_network_transmit_bytes_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s')) """

    podMetricsDict = {} # List of podDataCollection objects
    timestampList = [] # List of scraped timestamps
    podNameList = [] # List of scraped pods

    # Create list of podDataCollection objects, with CPU vals:
    for pod in cpu5s['data']['result']:
        p = podDataCollection(pod['metric']['pod_name'])
        podNameList.append(pod['metric']['pod_name'])
        p.cpu5s = pod['values']
        podMetricsDict[p.podName] = p

    for tStamp, val in pod['values']:
        timestampList.append(tStamp)

    for pod in memWriteB5s['data']['result']:
        podMetricsDict[pod['metric']['pod_name']].memW5s = pod['values']
        
    for pod in memReadB5s['data']['result']:
        podMetricsDict[pod['metric']['pod_name']].memR5s = pod['values']  

    for pod in netWriteB5s['data']['result']:
        podMetricsDict[pod['metric']['pod_name']].netW5s = pod['values']   

    for pod in netReadB5s['data']['result']:
        podMetricsDict[pod['metric']['pod_name']].netR5s = pod['values']

    createRawCSVs(timestampList, podNameList, testDirPath, podMetricsDict)

def main():
    #construct & parse args
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True,
        help="Name of input file containing test params")
    ap.add_argument("-pName", "--promPod", required=True,
        help="Name of prometheus operator pod inside k8 cluster")
    ap.add_argument("-k8url", required=True,
        help="URL & port number of k8 cluster we are accessing")
    ap.add_argument("-locustF", required=True,
        help="Name of locust file to be used for this round of testing")
    # add more args here
    args = vars(ap.parse_args())
    #kubernetes setup
    config.load_kube_config()
    extensions_v1beta1 = client.ExtensionsV1beta1Api()
    clusterConfs = clusterInfo()
   
   # -------- Main testing loop Start ----------
    for line in open(args["file"]):
        lnArgs = [x.strip() for x in line.split(',')]
        if len(lnArgs) != 11: # change val to appropriate cnt later
            print("Skipping experiment %s, wrong number of args" % lnArgs[0])
            continue
        exp_Nm = lnArgs[0]
        runtime = lnArgs[1]
        clientCnt = lnArgs[2]
        hatchRate = lnArgs[3]
        clusterConfs.interferenceZone = lnArgs[4]
        clusterConfs.interferenceLvl = lnArgs[5]
        clusterConfs.workflowDeplList['cart'] = lnArgs[6]
        clusterConfs.workflowDeplList['catalogue'] = lnArgs[7]
        clusterConfs.workflowDeplList['shipping'] = lnArgs[8]
        start_po = lnArgs[9]
        end_po = lnArgs[10]
        # add more var defs here ^ if more args get added to lines (like node color interference is on)
        print("Current running experiment: %s\n" % exp_Nm)
        testDirPath = testDirInit(exp_Nm) #Create current test's directory
        locustDur = runtime + "s"
        
        # setup cluster using input params
        print("Configuring cluster to match experiment input\n")
        clusterSetup(extensions_v1beta1, clusterConfs)
        print("5 second grace period\n")
        time.sleep(20)

        # build locust command to run locust
        locustCmd = "locust --host http://" + args["k8url"] + " -f " + args["locustF"] + " -c " + clientCnt + " -r " + hatchRate + " -t " + locustDur + " --no-web --only-summary --csv=locust"
        locustArgs = shlex.split(locustCmd)
        print("locust Command: %s\n" % locustCmd)
        print("locust CMD args: %s\n" % locustArgs)
        # TODO: Later: confirm cluster is setup properly

        # Get time-stamp before running test
        print("Test %s start\n" % exp_Nm)

        # TODO: add perfstat shell cmd in 
        
        startT = time.time() 
        
        # Exec locust command, exporting to CSV file & using params passed in through testParam file
        locustResultFNm = testDirPath + "/LocustLog.txt"
        with open(locustResultFNm, 'w+') as locust_f:
            p = subprocess.call(locustArgs, stdout=locust_f, stderr=locust_f, shell=False)
        
        # Once locust command finishes, get end timestamp
        stopT = time.time()
        moveLocustResults(testDirPath)
        # TODO: Exec kubectl port forward to prometheus pod ?? (currently, command is being run in separate terminal window)
        
        # Exec Prometheus API query(s) to gather metrics & build resulting csv files
        promQueries(startT, stopT, testDirPath)
        

main()
