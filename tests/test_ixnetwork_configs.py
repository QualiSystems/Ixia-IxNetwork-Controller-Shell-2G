
from shellfoundry.releasetools.test_helper import get_namespace_from_cloudshell_config


namespace = get_namespace_from_cloudshell_config()

ports_40 = ['IxVM 8.40 1/Module1/Port2', 'IxVM 8.40 2/Module1/Port1']
ports_50 = ['IxVM 8.50 1/Module1/Port2', 'IxVM 8.50 2/Module1/Port1']
ports_90 = ['IxVM 9.00 1/Module1/Port2', 'IxVM 9.00 1/Module1/Port1']

linux_40 = '192.168.65.27:443'
linux_50 = '192.168.65.73:443'
linux_90 = '192.168.65.55:443'

windows_01 = '192.168.65.39:11009'
windows_40 = '192.168.65.68:11009'
windows_50 = '192.168.65.94:11009'
windows_90_http = 'localhost:11009'
windows_90_https = '192.168.65.25:11009'

cm_90 = '192.168.42.199:443'


server_properties = {linux_40: {'ports': ports_40, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_50: {'ports': ports_50, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_90: {'ports': ports_90, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     windows_40: {'ports': ports_40, 'auth': None, 'config_version': 'classic'},
                     windows_50: {'ports': ports_50, 'auth': None, 'config_version': 'classic'},
                     windows_90_http: {'ports': ports_90, 'auth': None, 'config_version': 'classic'},
                     windows_90_https: {'ports': ports_90, 'auth': None, 'config_version': 'classic'},
                     cm_90: {'ports': ports_90, 'auth': None, 'config_version': 'classic'}}
