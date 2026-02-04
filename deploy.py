#!/usr/bin/python
from mininet.net import Containernet
from mininet.cli import CLI
from mininet.log import info, setLogLevel
import subprocess
import time

def get_mysql_ip():
    """Get MySQL container IP address"""
    try:
        cmd = ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', 'mysql-iot-edu']
        result = subprocess.check_output(cmd).decode().strip()
        if result:
            return result
    except:
        pass
    
    # Default Docker bridge IPs
    return '172.17.0.2'

def create_network():
    setLogLevel('info')
    
    # ==============================================
    # STEP 1: Start MySQL (if not running)
    # ==============================================
    info('*** Checking MySQL...\n')
    
    # Check if MySQL is running
    result = subprocess.run(
        ['docker', 'ps', '-q', '--filter', 'name=mysql-iot-edu'],
        capture_output=True,
        text=True
    )
    
    if not result.stdout.strip():
        info('*** Starting MySQL container...\n')
        subprocess.run([
            'docker', 'run', '-d',
            '--name', 'mysql-iot-edu',
            '-p', '3306:3306',
            '-e', 'MYSQL_ROOT_PASSWORD=root',
            '-e', 'MYSQL_DATABASE=iot_edu',
            '-e', 'MYSQL_USER=IoT_EDU',
            '-e', 'MYSQL_PASSWORD=root',
            'mysql:8'
        ], capture_output=True)
        
        info('*** Waiting 20 seconds for MySQL to start...\n')
        time.sleep(20)
    
    # Get MySQL IP
    mysql_ip = get_mysql_ip()
    info(f'*** MySQL container IP: {mysql_ip}\n')
    
    # ==============================================
    # STEP 2: Create Containernet
    # ==============================================
    net = Containernet()
 
    
 
    br1 = net.addSwitch('br1')
    
    info('*** Creating containers (non-blocking)...\n')
    
    # Containers with keep-alive only
    backend = net.addDocker('backend',
                           dimage='myzoo/backend',
                           ip='172.20.0.20',
                           dcmd='tail -f /dev/null',  # Non-blocking
                           ports=[8000],
                           port_bindings={8000: 8000},
                           environment={'MYSQL_HOST': mysql_ip})
    
    frontend = net.addDocker('frontend',
                            dimage='myzoo/frontend',
                            ip='172.20.0.30',
                            dcmd='tail -f /dev/null',  # Non-blocking
                            ports=[3000],
                            port_bindings={3000: 3000})
    
    zeek = net.addDocker('zeek',
                        dimage='myzoo/monitor_zeek',
                        ip='172.20.0.40',
                        ports=[47760, 80, 8090],
                        port_bindings={47760: 47760, 80: 80, 8090: 8090},
                        privileged=True)
    
    # Attack container
    ataque = net.addDocker('ataque',
                          dimage='myzoo/ataque',
                          ip='172.20.0.60')
    
    for container in [backend, frontend, zeek, ataque]:
        net.addLink(container, br1)
    
    net.start()
    
    # ==============================================
    # START SERVICES AFTER NETWORK IS READY
    # ==============================================
    info('*** Starting services in background...\n')
    
    # Function to start service safely
    def start_service(container, start_cmd, service_name, log_file):
        info(f'*** Starting {service_name}...\n')
        
        # Try multiple start methods
        start_methods = [
            f'cd /app && nohup {start_cmd} > {log_file} 2>&1 &',
            f'cd /app && {start_cmd} > {log_file} 2>&1 &',
            f'bash -c "cd /app && {start_cmd} &"'
        ]
        
        for method in start_methods:
            container.cmd(method)
            time.sleep(2)
            
            # Check if started
            check = container.cmd(f'ps aux | grep -v grep | grep -E "python|node|{service_name}" | wc -l')

    
    # Start all services
    start_service(backend, './start.sh', 'backend', '/var/log/backend.log')
    start_service(frontend, 'npm start', 'frontend', '/var/log/frontend.log')
    
    # Start Zeek
    zeek.cmd('/opt/zeek/bin/zeek -i eth0 local > /var/log/zeek.log 2>&1 &')
    
    # Wait and verify
    time.sleep(3)
    
    info('*** Service Status:\n')
    for name, container, port in [('backend', backend, 8000), ('frontend', frontend, 3000)]:
        processes = container.cmd('ps aux | grep -v grep | wc -l')
        test = container.cmd(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{port} || echo "000"')
        info(f'{name}: Processes={processes.strip()}, HTTP={test.strip()}\n')
    
    info('\n' + '='*60 + '\n')
    info('*** NETWORK READY ***\n')
    info('Services are running in background\n')
    info('Access:\n')
    info('  Frontend: http://localhost:3000\n')
    info('  Backend:  http://localhost:8000\n')
    info('\nDebug commands in Mininet CLI:\n')
    info('  backend tail -f /var/log/backend.log\n')
    info('  backend ps aux\n')
    info('='*60 + '\n')
    
    CLI(net)
    
    # Cleanup
    info('*** Stopping services...\n')
    backend.cmd('pkill -f "python.*start\|uvicorn\|gunicorn"')
    frontend.cmd('pkill -f "node\|npm"')
    
    net.stop()

if __name__ == '__main__':
    create_network()
