import os
import paramiko
paramiko.util.log_to_file('/tmp/paramiko.log')
paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))


def copy_remote_to_local(host,files,local_path):
    username = "joy"
    port = 22
    remote_images_path="/home/joy/"
    #local_path="./"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username)
    sftp = ssh.open_sftp()
    print("begin copy")
    for file in files:
        file_remote = remote_images_path + file
        file_local = os.path.join(local_path , file)
        print file_remote + '>>>' + file_local
        sftp.get(file_remote, file_local)
    
    sftp.close()
    ssh.close()



def test():
    copy_remote_to_local("kubenode-1",["demo"])


if __name__ == "__main__":
    test()
