import time
import pexpect
import subprocess
import sys
import re

class HcidumpError(Exception):
    """This exception is raised, when hcidump fails to start."""
    pass


class Hcidump:
    """A wrapper for hcidump utility."""

    def __init__(self):
        #out = subprocess.check_output("rfkill unblock bluetooth", shell = True)
        self.child = pexpect.spawn('sudo /bin/bash -c "sudo hcidump --raw -i hci0 | grep -E -e \'^>.{51}\s$\'"')
        open("hcidump.log", "w").close()
        logfile = open("hcidump.log", "a")
        self.child.logfile = logfile

    def __del__(self):
        subprocess.call(["sudo", "kill", str(self.child.pid)])

    def get_output(self):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        #self.child.send("\n")
        while True:
            try:
                self.child.expect(["> ", pexpect.EOF], timeout=5)
                return self.child.before.split("\r\n")
            except pexpect.TIMEOUT, e:
                print("child: " + str(self.child))
                continue


#if __name__ == "__main__":
#    print("Init hcidump...")
#    hcidump = Hcidump()
#    print("Ready!")
#    while True:
#        line = hcidump.get_output()
#        #print(str(len(line[0])))
#        print(line[0] + ", " + str(len(line[0])))
