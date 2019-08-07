import os
import time


def run():
    f = open('./trace/mm-link-scripts-file.txt', mode='r')
    traces = []
    for line in f:
        traces.append(line.split('\n')[0])
    f.close()
    subdirs = []
    for tt in traces:
        trace_name = tt.split(' ')[1].split('/')[2].split('.')[0]
        subdir = trace_name.split('_')[0] + "_" + trace_name.split('_')[3] + "_" + trace_name.split('_')[
            5] + '_file_compete'
        subdirs.append(subdir)

    # rl_algorithm = ['rl']
    algorithms = ['gcc', 'remyCC', 'indigo', 'pcc_rl', 'bbr', 'pcc_vivace', 'il', 'rl']
    print subdirs

    for kk in range(len(subdirs)):
        for ii in range(len(algorithms)):
            for jj in range(ii + 1, len(algorithms)):
                if algorithms[ii] == 'bbr' and algorithms[jj] == 'pcc_vivace':
                    pass
                else:
                    begin = time.time()
                    cc_vs_cmd = './multi_servers.py ' + subdirs[kk] + "_" + algorithms[ii] + "_VS_" + algorithms[jj]
                    server_cmd = cc_vs_cmd + " " + algorithms[ii] + " " + algorithms[jj]
                    print server_cmd
                    os.system(server_cmd)
                    while True:
                        if time.time() - begin > 150:
                            break
                    print (algorithms[ii], algorithms[jj], 'done')

        time.sleep(1)


if __name__ == '__main__':
    run()
