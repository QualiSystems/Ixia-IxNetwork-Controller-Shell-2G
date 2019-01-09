from cloudshell.traffic.driver import TrafficControllerDriver
import cloudshell.traffic.tg_helper as tg_helper

from ixn_handler import IxnHandler


class IxiaIxnetworkControllerShell2GDriver(TrafficControllerDriver):
    SHELL_TYPE = "CS_TrafficGeneratorController"
    SHELL_NAME = "Ixia IxNetwork Controller Shell 2G"

    def __init__(self):
        super(IxiaIxnetworkControllerShell2GDriver, self).__init__()
        self.handler = IxnHandler()

    def initialize(self, context):
        """

        :param context: ResourceCommandContext,ReservationContextDetailsobject with all Resource Attributes inside
        :type context:  context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        return 'Finished initializing'

    def load_config(self, context, config_file_location):
        """Reserve ports and load configuration

        :param context:
        :param str config_file_location: configuration file location
        :return:
        """
        self.logger.info('ixn_config_file_name = ' + config_file_location)
        super(IxiaIxnetworkControllerShell2GDriver, self).load_config(context)
        self.handler.load_config(context, config_file_location)

        return config_file_location + ' loaded, ports reserved'

    def start_traffic(self, context, blocking):
        """Start traffic on all ports

        :param context: the context the command runs on
        :param bool blocking: True - return after traffic finish to run, False - return immediately
        """
        self.handler.start_traffic(blocking)

    def stop_traffic(self, context):
        """Stop traffic on all ports

        :param context: the context the command runs on
        """
        self.handler.stop_traffic()

    def get_statistics(self, context, view_name, output_type):
        """Get real time statistics as sandbox attachment

        :param context:
        :param str view_name: requested view name
        :param str output_type: CSV or JSON
        :return:
        """
        return self.handler.get_statistics(context, view_name, output_type)

    def send_arp(self, context):
        """Send ARP/ND for all protocols

        :param context:
        :return:
        """
        self.handler.send_arp()

    def start_protocols(self, context):
        """Start all protocols

        :param context:
        :return:
        """
        self.handler.start_protocols()

    def stop_protocols(self, context):
        """Stop all protocols

        :param context:
        :return:
        """
        self.handler.stop_protocols()

    def run_quick_test(self, context, test):
        """Run quick test

        :param context:
        :param test: name of quick test to run
        :return:
        """
        quick_test_resut = self.handler.run_quick_test(context, test)
        tg_helper.write_to_reservation_out(context, 'Quick test result = ' + quick_test_resut)

        return quick_test_resut

    def get_session_id(self, context):
        """API only command to get REST session ID

        :param context:
        :return:
        """
        return self.handler.get_session_id()

    def get_children(self, context, obj_ref, child_type):
        """API only command to get list of children

        :param context:
        :param str obj_ref: valid object reference
        :param str child_type: requested children type. If None returns all children
        :return:
        """
        return self.handler.get_children(obj_ref, child_type)

    def get_attributes(self, context, obj_ref):
        """API only command to get object attributes

        :param context:
        :param str obj_ref: valid object reference
        :return:
        """
        return self.handler.get_attributes(obj_ref)

    def set_attribute(self, context, obj_ref, attr_name, attr_value):
        """API only command to set traffic generator object attribute

        :param context:
        :param str obj_ref: valid object reference
        :param str attr_name: attribute name
        :param str attr_value: attribute value
        :return:
        """
        self.handler.set_attribute(obj_ref, attr_name, attr_value)

    def cleanup_reservation(self, context):
        """Clear reservation when it ends

        :param context:
        :return:
        """
        pass

    def cleanup(self, context):
        """

        :param context:
        :return:
        """
        pass

    def keep_alive(self, context, cancellation_context):
        """

        :param context:
        :param cancellation_context:
        :return:
        """
        pass
