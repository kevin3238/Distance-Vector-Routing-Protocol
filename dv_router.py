"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16

#RoutePacket.destination = route is for getting to A
#Packet.dst = packet should be forwarded to A

class DVRouter(basics.DVRouterBase):
    NO_LOG = True # Set to True on an instance to disable its logging
    POISON_MODE = True # Can override POISON_MODE here
    DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.

        """
        # Starts calling handle_timer() at correct rate
        self.start_timer() 
        #dictionary that holds source, and dist/port for each destination
        #{dest1: [dist, out_port, start_time, host/not-host], dest2: [dist, out_port, start_time, host/not-host]}
        self.destination_map = {}
        self.destination_map[self] = [0, -1, api.current_time(), False]
        # self.destination_map.setdefault(self, [])
        # self.destination_map[self].append(0)
        # self.destination_map[self].append(-1)
        # self.destination_map[self].append(api.current_time())
        # self.destination_map[self].append(False)

        #port/latency pair
        self.port_latency = {}



    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        #add port/latency pair
        self.port_latency[port] = latency

        #Send RoutePacket to every destination including itself
        for dest in self.destination_map:
            destination = dest
            latency = self.destination_map.get(dest)[0]
            rPacket = basics.RoutePacket(destination, latency)
            self.send(rPacket, port)


    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        #poison the route then wait for replacement route via RoutePacket
        for dest in self.destination_map.keys():
            if self.destination_map.get(dest)[1] == port:
                self.destination_map.get(dest)[0] = INFINITY
                rPacket = basics.RoutePacket(dest, INFINITY)
                self.send(rPacket, port, flood = True)

        del self.port_latency[port]

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """

        # print(self)
        # if isinstance(packet, basics.Ping):
        #     print (self)
        #     print (packet.dst)
        #     print(self.destination_map)

        # if isinstance(packet, basics.Pong):
        #     print (self)

        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):

            dest = packet.destination
            latency = packet.latency
            source = packet.src
            total_dist = packet.latency + self.port_latency[port]

            #establish neighbor

            #route already exists to destination
            if dest in self.destination_map:
                #route has cost of INFINITY
                if latency == INFINITY and port == self.destination_map.get(dest)[1]:
                    self.destination_map.get(dest)[0] = INFINITY
                    self.destination_map.get(dest)[1] = port
                    self.destination_map.get(dest)[2] = api.current_time()
                    self.destination_map.get(dest)[3] = False
                #shorter distance, then update
                elif total_dist < self.destination_map.get(dest)[0]:
                    self.destination_map.get(dest)[0] = total_dist
                    self.destination_map.get(dest)[1] = port
                    self.destination_map.get(dest)[2] = api.current_time()
                    self.destination_map.get(dest)[3] = False

                #refresh route time if same route so that neighbors are remembered forever
                #since RoutePackets will constantly be sent to this router
                elif total_dist == self.destination_map.get(dest)[0] and port == self.destination_map.get(dest)[1]:
                    self.destination_map.get(dest)[2] = api.current_time()

            #no route to that particular destination yet
            else: 
                self.destination_map.setdefault(dest, [])
                self.destination_map[dest] = [total_dist, port, api.current_time(), False]
                # self.destination_map[dest].append(total_dist)
                # self.destination_map[dest].append(port)
                # self.destination_map[dest].append(api.current_time())
                # self.destination_map[self].append(False)

        elif isinstance(packet, basics.HostDiscoveryPacket):

                source = packet.src

                if source not in self.destination_map.keys():
                    self.destination_map.setdefault(source, [])
                    self.destination_map[source] = [self.port_latency[port], port, api.current_time(), True]
                    # self.destination_map[source].append(self.port_latency[port])
                    # self.destination_map[source].append(port)
                    # self.destination_map[source].append(api.current_time())
                    # self.destination_map[source].append(True)
                else:
                    if self.port_latency[port] < self.destination_map.get(source)[0]:
                        self.destination_map[source] = [self.port_latency[port], port, api.current_time(), True]
                        # self.destination_map.setdefault(source, [])
                        # self.destination_map[source].append(self.port_latency[port])
                        # self.destination_map[source].append(port)
                        # self.destination_map[source].append(api.current_time())
                        # self.destination_map[self].append(True)
        
        #regular packets; only forward if out_port != in_port
        else:
            #ping
            if isinstance(packet, basics.Ping):
                if packet.dst == self:
                    temp_pong = basics.Pong(packet)
                    self.send(temp_pong, port)
                else:
                    if packet.dst in self.destination_map:
                        out_port = self.destination_map.get(packet.dst)[1]
                        if out_port != port and self.destination_map.get(packet.dst)[0] < INFINITY:
                            self.send(packet, out_port, flood = False)
            #pong
            else: 
                if packet.dst in self.destination_map:
                    out_port = self.destination_map.get(packet.dst)[1]
                    if out_port != port and packet.dst != self and self.destination_map.get(packet.dst)[0] < INFINITY:
                        self.send(packet, out_port, flood = False)



    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """

        # check through the routes and see if 15 seconds have passed -> remove route
        for dest in self.destination_map.keys():
            if dest == self:
                self.destination_map.get(dest)[2] = api.current_time()

            if self.destination_map.get(dest)[3] == True:
                self.destination_map.get(dest)[2] = api.current_time()

            if api.current_time() - self.destination_map.get(dest)[2] >= self.ROUTE_TIMEOUT:
                del self.destination_map[dest]

        #send updated routes to neighbors/ poison stuff
        for port in self.port_latency:
            for dest in self.destination_map:
                #if dest is itself, send with latency 0
                if self.destination_map.get(dest)[0] == 0:
                    latency = 0
                    destination = dest
                    rPacket = basics.RoutePacket(destination, latency)
                    self.send(rPacket, port)
                    continue

                #poison mode
                if self.POISON_MODE:
                    #same port that the route uses, advertise dist of INFINITY
                    if port == self.destination_map.get(dest)[1]:
                        destination = dest
                        latency = INFINITY
                        rPacket = basics.RoutePacket(destination, latency)
                        self.send(rPacket, port)
                    #different port than the one route uses
                    elif port != self.destination_map.get(dest)[1]:
                        latency = self.destination_map.get(dest)[0]
                        destination = dest
                        rPacket = basics.RoutePacket(destination, latency)
                        self.send(rPacket, port)
                
                #not poison mode
                else:
                    #same port that the route uses, don't advertise route
                    if port == dest[1]:
                        continue
                    #different port than the one route uses
                    elif port != dest[1]:
                        latency = self.destination_map.get(dest)[0]
                        destination = dest
                        rPacket = basics.RoutePacket(destination, latency)
                        self.send(rPacket, port)

