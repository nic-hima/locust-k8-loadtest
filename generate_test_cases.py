# usage:

#python generate_test_case.py <output_file>
#output_format 

#test_id, #duration, #rate, #connection, #zone, #interference_level, #cart,#catalogue,#shipping,#start_pos, #end_pos


import sys
from datetime import date 
duration = 300 #sec
cart_pod = 1
catalogue_pod = 1
shipping_pod = 1
start_position = 5
end_position = 35

output_file = "default_test_case.csv"
if len(sys.argv) >1 :
    output_file  = sys.argv[1] 





zones = ['red','green','blue']
interference_level = [0,2,4]
connections = [125,250,500,1000,2000,4000]
#rate = max(connections)//4


# variables - zone, interference_level, connection
with open(output_file,'w' )as f:
    for zone in zones:
        for i_level in interference_level:
            for con in connections:
                rate = con//4

                today = date.today()
                config = "{}:{}:{}".format(cart_pod,catalogue_pod,shipping_pod)
                date_prefix = today.strftime("%b%d")
                test_id = "{}_{}_{}_{}_{}".format(date_prefix,zone,con,i_level,config) 
                data = "{},{},{},{},{},{},{},{},{},{},{}\n".format(test_id,duration,rate,con,zone,i_level,cart_pod,catalogue_pod,shipping_pod,start_position,end_position)
                f.write(data)
                print(data)





