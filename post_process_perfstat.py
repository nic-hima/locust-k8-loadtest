from itertools import islice
import sys
import pandas as pd
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")


def write_to_csv(dataframe,header,output_file):
    df = pd.DataFrame(dataframe, columns=header)
    df.to_csv(output_file+".csv",index=False)

def post_process_perfstat(filename):
    df = []
    N = 2
    output_file = filename.split('.temp')[0] #ommitting the temp part of the input file
    hostname = filename.split('/')[-1].split('_')[0]  #hostname
    #print("filename",filename) 
    with open(filename, 'r') as infile:
        while(True):
            lines_gen = list(islice(infile, N))
            #skip first two lines
            if N==2:
                N=3
                continue
            #break if end
            if len(lines_gen)==0:
                break
            # keep reading 3 lines at a time
            record = []
            for line in lines_gen:
                record.append(line.split(',')[1])
            
            record.append(hostname) 
            print record
            df.append(record)
    header=["cycle","instructions","LLC-load-misses","hostname"]
    write_to_csv(df,header,output_file)



if __name__ == "__main__":
    filename = sys.argv[1]
    post_process_perfstat(filename) 
