import socket
from flask import Flask, Response
import psutil
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
import time
from threading import Thread

class SystemMetricsCollector:
    def __init__(self, app: Flask = None):
        # CPU metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent', 
            'CPU Usage in Percent',
            ['cpu_type']  # user, system, idle
        )
        
        # Memory metrics
        self.memory_usage = Gauge(
            'system_memory_bytes',
            'Memory Usage in Bytes',
            ['type']  # used, free, cached, total
        )
        
        # Disk metrics
        self.disk_usage = Gauge(
            'system_disk_bytes',
            'Disk Usage in Bytes',
            ['mount_point', 'type']  # used, free, total
        )
        
        self.disk_io = Counter(
            'system_disk_io_bytes',
            'Disk I/O in Bytes',
            ['operation']  # read, write
        )
        
        # Network metrics
        self.network_traffic = Counter(
            'system_network_traffic_bytes',
            'Network Traffic in Bytes',
            ['interface', 'direction']  # received, transmitted
        )
        
        self.network_connections = Gauge(
            'system_network_connections',
            'Number of Network Connections',
            ['protocol', 'status']  # tcp/udp, ESTABLISHED/LISTEN/etc
        )
        
        # Register Flask app endpoint if provided
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Register the metrics endpoint with a Flask app"""
        @app.route('/metrics')
        def metrics():
            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    def collect_cpu_metrics(self):
        """Collect CPU metrics"""
        cpu_times = psutil.cpu_times_percent()
        self.cpu_usage.labels(cpu_type='user').set(cpu_times.user)
        self.cpu_usage.labels(cpu_type='system').set(cpu_times.system)
        self.cpu_usage.labels(cpu_type='idle').set(cpu_times.idle)

    def collect_memory_metrics(self):
        """Collect memory metrics"""
        mem = psutil.virtual_memory()
        self.memory_usage.labels(type='total').set(mem.total)
        self.memory_usage.labels(type='used').set(mem.used)
        self.memory_usage.labels(type='free').set(mem.free)
        self.memory_usage.labels(type='cached').set(mem.cached)

    def collect_disk_metrics(self):
        """Collect disk metrics"""
        # Disk usage
        for partition in psutil.disk_partitions():
            if partition.fstype:
                usage = psutil.disk_usage(partition.mountpoint)
                self.disk_usage.labels(
                    mount_point=partition.mountpoint, 
                    type='total'
                ).set(usage.total)
                self.disk_usage.labels(
                    mount_point=partition.mountpoint, 
                    type='used'
                ).set(usage.used)
                self.disk_usage.labels(
                    mount_point=partition.mountpoint, 
                    type='free'
                ).set(usage.free)
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        self.disk_io.labels(operation='read').inc(disk_io.read_bytes)
        self.disk_io.labels(operation='write').inc(disk_io.write_bytes)

    def collect_network_metrics(self):
        """Collect network metrics"""
        # Network traffic
        net_io = psutil.net_io_counters(pernic=True)
        for interface, counters in net_io.items():
            self.network_traffic.labels(
                interface=interface, 
                direction='received'
            ).inc(counters.bytes_recv)
            self.network_traffic.labels(
                interface=interface, 
                direction='transmitted'
            ).inc(counters.bytes_sent)
        
        # Network connections
        connections = psutil.net_connections()
        conn_count = {'tcp': {}, 'udp': {}}
        for conn in connections:
            proto = 'tcp' if conn.type == socket.SOCK_STREAM else 'udp'
            status = conn.status
            conn_count[proto][status] = conn_count[proto].get(status, 0) + 1
        
        for proto in conn_count:
            for status, count in conn_count[proto].items():
                self.network_connections.labels(
                    protocol=proto,
                    status=status
                ).set(count)

    def collect_metrics(self):
        """Collect all metrics periodically"""
        while True:
            try:
                self.collect_cpu_metrics()
                self.collect_memory_metrics()
                self.collect_disk_metrics()
                self.collect_network_metrics()
            except Exception as e:
                print(f"Error collecting metrics: {e}")
            time.sleep(15)  # Collect metrics every 15 seconds

    def start_collecting(self):
        """Start a thread to collect metrics"""
        thread = Thread(target=self.collect_metrics)
        thread.daemon = True
        thread.start()
