import os
import sys
import subprocess
from datetime import datetime

def history():
    #os.environ['HISTTIMEFORMAT'] = "%Y-%d-%m_%H:%M  "
    if 'HISTFILE' in os.environ:
        filename = os.path.expandvars("$HISTFILE")
    else:
        filename = os.path.expandvars("$HOME/.bash_history")
    with open(filename) as f:
        line = f.readline()
        aligned_line = []
        timestamp = ''
        cmd = []
        while line:
            items = line.split()
            if items:
                if items[0][0] == '#' and len(items[0]) == 11:
                    if timestamp and cmd:
                        aligned_line.append("{}  {}".format(timestamp, ' '.join(cmd)))
                    timestamp = datetime.fromtimestamp(int(items[0][1:])).strftime("%Y-%m-%d_%H:%M:%S")
                    cmd = []
                else:
                    cmd += items
            line = f.readline()
    return aligned_line

def gitlog():

    cmd = ['trgit', 'log', '--oneline', '--pretty=format:%cd  trgit show %h #%d %s <%an>', '--date=format:%Y-%m-%d_%H:%M:%S']
    return subprocess.check_output(cmd).decode("utf-8").splitlines()

def main():
    output = history() + gitlog()
    output.sort()
    verbose = False
    for l in output:
        print(l)
        if 'trgit show' in l and verbose:
            cmd = l.split()[1:4]
            subprocess.call(cmd)

if __name__ == "__main__":
    main()
