''' Current assumptions:
    1. Only 1 instance of each microservice on the cluster (at the moment)

'''
import os
import sys
import argparse
import shlex, subprocess
import datetime
import time
from  prometheus_http_client import Prometheus

#TODO: Add ability to place interference pods on specific nodes in cluster
#TODO: Add ability to scale different number of pods for each micro-service
#TODO: Figure out strategy for pod isolation on nodes when applying interference to those specific pod(s)

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

    prom = Prometheus()

    # TODO: parse input file for test params
    for line in open(args["file"]):
        lnArgs = [x.strip() for x in line.split(' ')]
        if len(lnArgs) != 4: # change val to appropriate cnt later
            print("Skipping experiment %s, wrong number of args" % lnArgs[0])
            continue
        exp_Nm = lnArgs[0]
        runtime = lnArgs[1]
        clientCnt = lnArgs[2]
        hatchRate = lnArgs[3]
        # add more var defs here if more args get added to lines (like node color interference is on)
        print("Current running experiment: %s\n" % exp_Nm)
        # TODO Later: based on input params, alter cluster config w/ kubectl commands
        # TODO: build locust command to run locust
        locustCmd = "locust --host http://" + args["k8url"] + " -f " + args["locustF"] + " -c " + clientCnt + " -r " + hatchRate + " -t " + runtime + " --no-web --only-summary --csv=" + exp_Nm
        locustArgs = shlex.split(locustCmd)
        print("locust Command: %s\n" % locustCmd)
        print("locust CMD args: %s\n" % locustArgs)
        # TODO Later: confirm cluster is setup properly
        # TODO: Get time-stamp before running test
        print("Test %s start\n" % exp_Nm)
        startTime = time.time() 
        
        # TODO: Exec locust command, exporting to CSV file named according to input vals from file
        locustResultFNm = exp_Nm + ".txt"
        with open(locustResultFNm, 'w+') as locust_f:
            p = subprocess.call(locustArgs, stdout=locust_f, stderr=locust_f, shell=False)
        # TODO: Once locust command finishes, get end timestamp
        stopTime = time.time()
        
    # TODO: Exec kubectl port forward to prometheus pod ?? (currently, command is being run in separate terminal window)
    # TODO: Exec Prometheus API query(s) to gather metrics (delivered in JSON)
        # cpu = prom.query_rang(metric='sum(rate(container_cpu_usage_seconds_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s')
        cpu = prom.query_rang(metric='(container_cpu_usage_seconds_total{namespace="robot-shop"}[1m]) by (pod_name)', start=startTime, end=stopTime, step='5s')
        memWrite = prom.query_rang(metric='sum(rate(container_fs_writes_bytes_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s')
        memRead = prom.query_rang(metric='sum(rate(container_fs_reads_bytes_total{namespace="robot-shop"}[1m])) by (pod_name)', start=startTime, end=stopTime, step='5s')

        print(cpu)
        print("\n")
        print(memWrite)
        print("\n")
        print(memRead)
    # TODO: Decode JSON responses & build data CSV file

main()
