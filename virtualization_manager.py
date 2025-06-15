import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import random

class VirtualizationManager:
    def __init__(self, num_servers: int = 20):
        self.num_servers = num_servers
        self.servers = {}
        self.last_fault_time = datetime.now()
        self.fault_interval = timedelta(minutes=2)  # Generate fault every 2 minutes
        self.initialize_servers()
        self.create_initial_vms()  # Add initial VMs
        
    def initialize_servers(self):
        """Initialize server states with realistic workload patterns."""
        for i in range(self.num_servers):
            server_id = f"Rack-{i+1}"
            # Initialize with realistic base loads
            base_load = np.random.normal(30, 10)  # Base load between 20-40%
            
            # Make some racks idle initially
            is_idle = random.random() < 0.2  # 20% chance of being idle
            
            self.servers[server_id] = {
                'cpu_usage': base_load if not is_idle else 5,
                'memory_usage': base_load * 1.2 if not is_idle else 10,
                'network_load': base_load * 0.8 if not is_idle else 3,
                'virtual_machines': [],
                'status': 'active',
                'power_state': 'idle' if is_idle else 'normal',
                'temperature': np.random.normal(35, 2),
                'can_host_vms': True,
                'maintenance_start': None,
                'maintenance_type': None,
                'has_fault': False,
                'fault_type': None
            }

    def create_initial_vms(self):
        """Create initial virtual machines for some servers."""
        active_servers = [sid for sid, s in self.servers.items() 
                         if s['status'] == 'active' and s['power_state'] != 'idle']
        
        # Create VMs for 60% of active servers
        for server_id in random.sample(active_servers, k=int(len(active_servers) * 0.6)):
            num_vms = random.randint(1, 3)  # Create 1-3 VMs per server
            for _ in range(num_vms):
                source_server = random.choice(active_servers)
                vm_load = random.uniform(10, 30)
                vm_id = f"VM-{source_server}-{datetime.now().strftime('%H%M%S')}"
                
                self.servers[server_id]['virtual_machines'].append({
                    'id': vm_id,
                    'source_server': source_server,
                    'cpu_load': vm_load,
                    'memory_load': vm_load * 1.2,
                    'network_load': vm_load * 0.8
                })
                
                # Update server loads
                self.servers[server_id]['cpu_usage'] += vm_load
                self.servers[server_id]['memory_usage'] += vm_load * 1.2
                self.servers[server_id]['network_load'] += vm_load * 0.8
    
    def update_server_loads(self):
        """Update server loads with realistic variations and generate random faults."""
        current_time = datetime.now()
        active_servers = [sid for sid, s in self.servers.items() if s['status'] == 'active']
        
        # Generate random fault every 2 minutes
        if current_time - self.last_fault_time >= self.fault_interval:
            self.generate_random_fault()
            self.last_fault_time = current_time
        
        # Process maintenance completion
        for server_id in active_servers:
            if (self.servers[server_id]['maintenance_start'] and 
                current_time - self.servers[server_id]['maintenance_start'] >= timedelta(minutes=1)):
                # Reset after maintenance
                self.servers[server_id]['maintenance_start'] = None
                self.servers[server_id]['maintenance_type'] = None
                self.servers[server_id]['temperature'] = np.random.normal(35, 2)
                self.servers[server_id]['status'] = 'active'
                self.servers[server_id]['power_state'] = 'normal'
                self.servers[server_id]['has_fault'] = False
                self.servers[server_id]['fault_type'] = None
        
        # Update loads for active servers
        for server_id in active_servers:
            if self.servers[server_id]['maintenance_start']:
                continue  # Skip updates for servers under maintenance
                
            # Add some random variation to loads
            if not self.servers[server_id]['has_fault']:
                variation = np.random.normal(0, 5)
                base_load = self.servers[server_id]['cpu_usage']
                
                # Calculate total VM load
                vm_load = sum(vm['cpu_load'] for vm in self.servers[server_id]['virtual_machines'])
                
                # Update loads considering both base load and VM load
                self.servers[server_id]['cpu_usage'] = np.clip(
                    base_load + variation + vm_load,
                    10, 95
                ) if self.servers[server_id]['power_state'] != 'idle' else 5
                
                # Memory changes more slowly
                mem_variation = variation * 0.5
                self.servers[server_id]['memory_usage'] = np.clip(
                    self.servers[server_id]['memory_usage'] + mem_variation + vm_load * 1.2,
                    20, 90
                ) if self.servers[server_id]['power_state'] != 'idle' else 10
                
                # Network load fluctuates more
                net_variation = variation * 1.5
                self.servers[server_id]['network_load'] = np.clip(
                    self.servers[server_id]['network_load'] + net_variation + vm_load * 0.8,
                    5, 100
                ) if self.servers[server_id]['power_state'] != 'idle' else 3
            
            # Update temperature based on load and fault status
            if self.servers[server_id]['power_state'] != 'idle':
                if self.servers[server_id]['has_fault'] and self.servers[server_id]['fault_type'] == 'temperature':
                    self.servers[server_id]['temperature'] = np.random.uniform(45, 50)
                else:
                    load_factor = self.servers[server_id]['cpu_usage'] / 100
                    self.servers[server_id]['temperature'] = np.clip(
                        35 + (load_factor * 10) + np.random.normal(0, 0.5),
                        30, 50
                    )
    
    def generate_random_fault(self):
        """Generate a random fault in one of the active servers."""
        active_servers = [sid for sid, s in self.servers.items() 
                         if s['status'] == 'active' and s['power_state'] != 'idle' 
                         and not s['maintenance_start'] and not s['has_fault']]
        
        if not active_servers:
            return
            
        faulty_server = random.choice(active_servers)
        fault_type = random.choice(['temperature', 'load', 'power'])
        
        self.servers[faulty_server]['has_fault'] = True
        self.servers[faulty_server]['fault_type'] = fault_type
        
        if fault_type == 'temperature':
            self.servers[faulty_server]['temperature'] = np.random.uniform(45, 50)
        elif fault_type == 'load':
            self.servers[faulty_server]['cpu_usage'] = np.random.uniform(90, 100)
            self.servers[faulty_server]['memory_usage'] = np.random.uniform(90, 100)
        else:  # power fault
            self.servers[faulty_server]['power_state'] = 'warning'
            self.servers[faulty_server]['temperature'] = np.random.uniform(42, 45)
    
    def start_maintenance(self, server_id: str, maintenance_type: str):
        """Start maintenance (repair/replace) for a server."""
        if server_id in self.servers:
            self.servers[server_id]['maintenance_start'] = datetime.now()
            self.servers[server_id]['maintenance_type'] = maintenance_type
            self.servers[server_id]['status'] = 'maintenance'
            
            # Migrate VMs to other servers
            self.migrate_vms_from_server(server_id)
    
    def migrate_vms_from_server(self, source_server_id: str):
        """Migrate VMs from a server under maintenance to other available servers."""
        vms_to_migrate = self.servers[source_server_id]['virtual_machines']
        available_servers = [sid for sid, s in self.servers.items() 
                           if (sid != source_server_id and s['status'] == 'active' 
                               and s['power_state'] != 'idle' and not s['maintenance_start'])]
        
        if not available_servers:
            return
        
        # Distribute VMs across available servers
        for vm in vms_to_migrate:
            target_server = random.choice(available_servers)
            self.servers[target_server]['virtual_machines'].append(vm)
            
            # Update target server loads
            self.servers[target_server]['cpu_usage'] = np.clip(
                self.servers[target_server]['cpu_usage'] + vm['cpu_load'],
                10, 95
            )
            self.servers[target_server]['memory_usage'] = np.clip(
                self.servers[target_server]['memory_usage'] + vm['memory_load'],
                20, 90
            )
            self.servers[target_server]['network_load'] = np.clip(
                self.servers[target_server]['network_load'] + vm['network_load'],
                5, 100
            )
        
        # Clear VMs from source server
        self.servers[source_server_id]['virtual_machines'] = []
    
    def optimize_workload(self):
        """Optimize workload distribution across servers."""
        active_servers = [sid for sid, s in self.servers.items() 
                         if s['status'] == 'active' and not s['maintenance_start']]
        
        # Sort servers by load
        servers_by_load = sorted(
            active_servers,
            key=lambda x: self.servers[x]['cpu_usage']
        )
        
        # Find overloaded and underutilized servers
        overloaded = [s for s in servers_by_load if self.servers[s]['cpu_usage'] > 80]
        underutilized = [s for s in servers_by_load if self.servers[s]['cpu_usage'] < 30]
        
        # Balance load
        for high_server in overloaded:
            if not underutilized:
                break
                
            for low_server in underutilized:
                if not self.servers[low_server]['can_host_vms']:
                    continue
                    
                # Calculate load to transfer
                load_to_transfer = (self.servers[high_server]['cpu_usage'] - 60) / 2
                
                # Create virtual machine on underutilized server
                vm_id = f"VM-{high_server}-{datetime.now().strftime('%H%M%S')}"
                self.servers[low_server]['virtual_machines'].append({
                    'id': vm_id,
                    'source_server': high_server,
                    'cpu_load': load_to_transfer,
                    'memory_load': load_to_transfer * 1.2,
                    'network_load': load_to_transfer * 0.8
                })
                
                # Update loads
                self.servers[high_server]['cpu_usage'] -= load_to_transfer
                self.servers[low_server]['cpu_usage'] += load_to_transfer
                
                if self.servers[low_server]['cpu_usage'] > 30:
                    underutilized.remove(low_server)
        
        # Put very underutilized servers into power saving mode
        for server_id in active_servers:
            if (self.servers[server_id]['cpu_usage'] < 15 and 
                not self.servers[server_id]['virtual_machines']):
                self.servers[server_id]['power_state'] = 'idle'
            elif self.servers[server_id]['power_state'] == 'idle':
                # Randomly wake up some idle servers
                if random.random() < 0.1:  # 10% chance to wake up
                    self.servers[server_id]['power_state'] = 'normal'
                    self.servers[server_id]['cpu_usage'] = np.random.normal(30, 10)
    
    def get_server_status(self) -> Dict:
        """Get current status of all servers."""
        return self.servers 