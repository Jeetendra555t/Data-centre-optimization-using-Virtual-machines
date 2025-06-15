
import random
import time

class Server:
    def __init__(self, id):
        self.id = id
        self.vms = []
        self.active = False

    def load(self):
        return sum(vm.load for vm in self.vms)

    def add_vm(self, vm):
        self.vms.append(vm)
        self.active = True

    def remove_vm(self, vm):
        self.vms.remove(vm)
        if not self.vms:
            self.active = False

class VM:
    def __init__(self, id, load):
        self.id = id
        self.load = load

class Cloudlet:
    def __init__(self, id, duration):
        self.id = id
        self.duration = duration

# Initialize servers and VMs
servers = [Server(i) for i in range(5)]
vms = [VM(i, random.randint(10, 30)) for i in range(10)]

# Initial random placement
for vm in vms:
    random.choice(servers).add_vm(vm)

def consolidate(servers):
    all_vms = [vm for server in servers for vm in server.vms]
    all_vms.sort(key=lambda x: x.load, reverse=True)
    for server in servers:
        server.vms = []
        server.active = False
    for vm in all_vms:
        for server in servers:
            if server.load() + vm.load <= 100:
                server.add_vm(vm)
                break

# Create cloudlets
cloudlets = [Cloudlet(i, random.uniform(0.1, 0.3)) for i in range(20)]

# Assign cloudlets to VMs and simulate execution
vm_list = [vm for server in servers for vm in server.vms]
for i, cloudlet in enumerate(cloudlets):
    vm = vm_list[i % len(vm_list)]
    print(f"Cloudlet {cloudlet.id} executing on VM {vm.id}...", end=' ')
    time.sleep(cloudlet.duration)
    print("Status: Success")

# Consolidation simulation
initial_active = sum(1 for s in servers if s.active)
consolidate(servers)
final_active = sum(1 for s in servers if s.active)

print(f"Initial active servers: {initial_active}")
print(f"Final active servers after consolidation: {final_active}")
