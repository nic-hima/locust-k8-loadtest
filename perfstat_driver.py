#format: python <script_name> exp_name total_duration output_dir

#from pssh.clients import ParallelSSHClient
from pprint import pprint
from pssh.clients.native import ParallelSSHClient
import sys
from pssh.utils import enable_logger, logger
from gevent import joinall
import time
import os
from sftp import copy_remote_to_local
from post_process_perfstat import post_process_perfstat
from collections import defaultdict
exp_name = sys.argv[1]
total_duration = int(sys.argv[2]) #given in seconds
output_dir = sys.argv[3]

total_duration_in_ms = total_duration * 1000 #scale to ms

#print ("debug>>", sys.argv)

hosts = ['kubenode-1','kubenode-2','kubenode-3','kubenode-4']
#hosts = ['kubenode-1']
user="joy"
client = ParallelSSHClient(hosts,user)

try:
   output = client.run_command('sh ./perfstat_node/perfstat.sh {} {}'.format(exp_name,total_duration_in_ms))
   #print ("debug>> executed")
except Exception as e:
   print e


time.sleep(total_duration) 


#print ("debug>> wakeup")
'''
for host, host_output in output.items():
    for line in host_output.stdout:
        print(line)
        print ("debug>>")
'''



#todo 
## copy the files from each server
## preprocess each file
## compiled to a single file 

print("start preprocessing")

#create the dir if not exist

if not os.path.exists(output_dir)==True:
    os.makedirs(output_dir)


vm_list = defaultdict(list)
vm_list['kubenode-1'] = ["kb-w11","kb-w12","kb-w13","kb-w14"]
vm_list['kubenode-2'] = ["kb-w21","kb-w22","kb-w23","kb-w24"]
vm_list['kubenode-3'] = ["kb-w31","kb-w32","kb-w33","kb-w34"]
vm_list['kubenode-4'] = ["kb-w41","kb-w42","kb-w43","kb-w44"]

file_list = []
list_of_kvm = ['kubenode-1','kubenode-2','kubenode-3','kubenode-4']
for node in list_of_kvm:
    list_of_vms = vm_list[node]
    fetch_files = []
    for vm in list_of_vms:
        fetch_files.append("{}_{}_perfstat.temp".format(vm,exp_name))
        file_list.append("{}_{}_perfstat.temp".format(vm,exp_name))
    copy_remote_to_local(node, fetch_files, output_dir)

for file in file_list:
    input_file = os.path.join(os.getcwd(),output_dir,file)
    post_process_perfstat(input_file)

