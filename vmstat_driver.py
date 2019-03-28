#format: python <script.py> exp_name total_duration output_dir start_position end_position

#from pssh.clients import ParallelSSHClient
from pprint import pprint
from pssh.clients.native import ParallelSSHClient
import sys
from pssh.utils import enable_logger, logger
from gevent import joinall
import time
import os
from vmstat_processor import process_vmstat
import paramiko
paramiko.util.log_to_file('/tmp/paramiko.log')
paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))


def copy_remote_to_local(host,infile,outfile,local_path):
    username = "cloudsys"
    port = 22
    remote_images_path="/home/cloudsys/"
    #local_path="./"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username)
    sftp = ssh.open_sftp()

    file_remote = os.path.join(remote_images_path,infile)
    file_local = os.path.join(local_path,outfile)

    sftp.get(file_remote, file_local)
    
    sftp.close()
    ssh.close()



def main():
    exp_name = sys.argv[1]
    total_duration = int(sys.argv[2])
    output_dir = sys.argv[3]
    start_position = int(sys.argv[4])
    end_position = int(sys.argv[5])
    interval=5
    cpu_frequency = total_duration //5
    user="cloudsys"



    hosts = []
    for i in xrange(1,5):
        for j in xrange(1,5):
            hosts.append("kb-w{}{}".format(i,j))

    client = ParallelSSHClient(hosts,user)

    try:
        output = client.run_command('vmstat  {} {} > {}_vmfile.tmp '.format(interval, cpu_frequency, exp_name))
    except Exception as e:
        print(e)


    time.sleep(total_duration)



    #create the dir if not exist

    if not os.path.exists(output_dir)==True:
        os.makedirs(output_dir)

    for vm in hosts:
        src_file_name = "{}_vmfile.tmp".format(exp_name)
        dst_file_name = "{}_vmfile.tmp".format(vm)
        print("trying to copy: {} {} {}".format(vm,src_file_name,dst_file_name,output_dir))
        copy_remote_to_local(vm,src_file_name, dst_file_name, output_dir)
        #post_process_outfile
        output_file = os.path.join(output_dir,"{}_vmfile.csv".format(vm))
        input_file = os.path.join(output_dir,"{}_vmfile.tmp".format(vm))
        print("debug: process_vmstat {} {} {} {}".format(input_file,start_position,end_position,output_file))
        process_vmstat(input_file,start_position,end_position, output_file)
    #call the post processing here



if __name__ == "__main__":
    main()