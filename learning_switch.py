"""
Your learning switch warm-up exercise for CS-168.

Start it up with a commandline like...

  ./simulator.py --default-switch-type=learning_switch topos.rand --links=0

"""

import sim.api as api
import sim.basics as basics


class LearningSwitch(api.Entity):
    """
    A learning switch.

    Looks at source addresses to learn where endpoints are.  When it doesn't
    know where the destination endpoint is, floods.

    This will surely have problems with topologies that have loops!  If only
    someone would invent a helpful poem for solving that problem...

    """

    def __init__(self):
        """
        Do some initialization.

        You probablty want to do something in this method.

        """
        # create dicitonary to keep track of host/port pair
        self.host_port_dict = {} 

    def handle_link_down(self, port):
        """
        Called when a port goes down (because a link is removed)

        You probably want to remove table entries which are no longer
        valid here.

        """
        
        #delete all hosts that have same port
        for host in self.host_port_dict.keys():
            if self.host_port_dict.get(host) == port:
                del self.host_port_dict[host]


    def handle_rx(self, packet, in_port):
        """
        Called when a packet is received.

        You most certainly want to process packets here, learning where
        they're from, and either forwarding them toward the destination
        or flooding them.

        """

        # The source of the packet can obviously be reached via the input port, so
        # we should "learn" that the source host is out that port.  If we later see
        # a packet with that host as the *destination*, we know where to send it!
        # But it's up to you to implement that.  For now, we just implement a
        # simple hub.

        if packet.src not in self.host_port_dict:
            self.host_port_dict[packet.src] = in_port
            
        if not isinstance(packet, basics.HostDiscoveryPacket):
            if packet.dst in self.host_port_dict:
                out_port = self.host_port_dict[packet.dst]

                if out_port != in_port:
                    self.send(packet, out_port, flood = False)
            else:
                self.send(packet, in_port, flood = True)

