import psutil
import time
from typing import Dict

class MetricsCollector:
    @staticmethod
    def collect_system_metrics() -> Dict:
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_io': psutil.disk_io_counters(),
            'network_io': psutil.net_io_counters()
        }

    @staticmethod
    def check_thresholds(metrics: Dict, config: Dict) -> bool:
        if metrics['cpu_percent'] > config['cpu_limit']:
            return False
        if metrics['memory_percent'] > config['memory_limit']:
            return False
        return True