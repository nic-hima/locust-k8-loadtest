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
exp_name = sys.argv[1]
total_duration = int(sys.argv[2])
output_dir = sys.argv[3]

total_duration *=1000
#print ("debug>>", sys.argv)

hosts = ['kubenode-1','kubenode-2','kubenode-3','kubenode-4']
#hosts = ['kubenode-1']
user="joy"
client = ParallelSSHClient(hosts,user)

try:
   output = client.run_command('sh ./perfstat_node/perfstat.sh {} {}'.format(exp_name,total_duration))
   #print ("debug>> executed")
except Exception as e:
   print e


time.sleep(total_duration//1000)
#time.sleep(total_duration)

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

try:
   output = client.run_command('virsh list')
except Exception as e:
   print e

for host, host_output in output.items():
    vm_list = []
    count = 0
    for line in host_output.stdout:
        if count >=2:
            if len(line.split())>=2:
                node_name = line.split()[1]
	        vm_list.append(node_name.encode('ascii','ignore'))
        count +=1 
    print vm_list
    file_list = []
    for vm in vm_list:
        outfile="{}_{}_perfstat.temp".format(vm,exp_name)
        file_list.append(outfile)
   
    copy_remote_to_local(host, file_list, output_dir)
    for file in file_list:
        input_file = os.path.join(os.getcwd(),output_dir,file)
        post_process_perfstat(input_file)




