
ports_840 = ['IxVM 8.40 1/Module1/Port2', 'IxVM 8.40 2/Module1/Port1']
ports_850 = ['ixia-850-1/Module1/Port2', 'ixia-850-1/Module1/Port1']
ports_900 = ['ixia-900-1/Module1/Port2', 'ixia-900-1/Module1/Port1']

linux_840 = '192.168.65.27:443'
linux_850 = '192.168.65.73:443'
linux_900 = '192.168.65.55:443'

windows_801 = '192.168.65.39:11009'
windows_840 = '192.168.65.68:11009'
windows_850 = '192.168.65.94:11009'
windows_900_http = 'localhost:11009'
windows_900_https = '192.168.65.25:11009'

cm_900 = '192.168.42.199:443'


server_properties = {linux_840: {'ports': ports_840, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_850: {'ports': ports_850, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     linux_900: {'ports': ports_900, 'auth': ('admin', 'admin'), 'config_version': 'ngpf'},
                     windows_840: {'ports': ports_840, 'auth': None, 'config_version': 'classic'},
                     windows_850: {'ports': ports_850, 'auth': None, 'config_version': 'classic'},
                     windows_900_http: {'ports': ports_900, 'auth': None, 'config_version': 'classic'},
                     windows_900_https: {'ports': ports_900, 'auth': None, 'config_version': 'classic'},
                     cm_900: {'ports': ports_900, 'auth': None, 'config_version': 'classic'}}
