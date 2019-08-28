from cloudshell.traffic.driver import TrafficControllerDriver
import cloudshell.traffic.tg_helper as tg_helper

from ixn_handler import IxnHandler


class IxNetworkControllerShell2GDriver(TrafficControllerDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.handler = IxnHandler()

    def load_config(self, context, config_file_location):
        """ Load IxNetwork configuration file and reserve ports.

        :param config_file_location: Full path to IxNetwork configuration file name - ixncfg
        """
        super(self.__class__, self).load_config(context)
        self.handler.load_config(context, config_file_location)

    def send_arp(self, context):
        """ Send ARP/ND for all interfaces (NA for Linux servers that supports only ngpf). """
        self.handler.send_arp()

    def start_protocols(self, context):
        """ Start all protocols (classic and ngpf) on all ports. """
        self.handler.start_protocols()

    def stop_protocols(self, context):
        """ Stop all protocols (classic and ngpf) on all ports. """
        self.handler.stop_protocols()

    def start_traffic(self, context, blocking):
        """ Start traffic on all ports.

        :param blocking: True - return after traffic finish to run, False - return immediately.
        """
        self.handler.start_traffic(blocking)
        return 'traffic started in {} mode'.format(blocking)

    def stop_traffic(self, context):
        """ Stop traffic on all ports. """
        self.handler.stop_traffic()

    def get_statistics(self, context, view_name, output_type):
        """ Get view statistics.

        :param view_name: port, traffic item, flow group etc.
        :param output_type: CSV or JSON.
        """
        return self.handler.get_statistics(context, view_name, output_type)

    def run_quick_test(self, context, test):
        """ Run quick test in blocking mode.

        :param test: name of quick test to run
        """
        quick_test_resut = self.handler.run_quick_test(context, test)
        tg_helper.write_to_reservation_out(context, 'Quick test result = ' + quick_test_resut)
        return quick_test_resut

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def cleanup_reservation(self, context):
        pass

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)

    #
    # Hidden commands for developers only.
    #

    def get_session_id(self, context):
        """ API only command to get REST session ID.

        return: session ID
        """
        return self.handler.get_session_id()

    def get_children(self, context, obj_ref, child_type):
        """ API only command to get list of children.

        :param str obj_ref: valid object reference
        :param str child_type: requested children type. If None returns all children
        :return: list(object references of children)
        """
        return self.handler.get_children(obj_ref, child_type)

    def get_attributes(self, context, obj_ref):
        """ API only command to get object attributes.

        :param str obj_ref: valid object reference
        :return: dict(key, values) of all attributes
        """
        return self.handler.get_attributes(obj_ref)

    def set_attribute(self, context, obj_ref, attr_name, attr_value):
        """ API only command to set traffic generator object attribute.

        :param str obj_ref: valid object reference
        :param str attr_name: attribute name
        :param str attr_value: attribute value
        """
        self.handler.set_attribute(obj_ref, attr_name, attr_value)
