import socket

# http://stackoverflow.com/questions/2838244/get-open-tcp-port-in-python/2838309#2838309
def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("",0))
        # not required
        # s.listen(1)
        return s.getsockname()[1]

if __name__ == '__main__':
    import sys
    how_many = int(sys.argv[1])
    print("The ports returned by free_port when run {} times"
          .format(how_many))
    for i in range(how_many):
        print(free_port())
    

# another idea but it's much more work for little more value
# class PortsPool:
# 
#     """
#     The PortsPool object scans for available (tcp) ports in the system.
#     
#     At creation time, caller specifies the set of ports to be monitores
#     In our case typically 2000-65536
#     
#     It initializes its cache from the output of
#     # ss -altn
#     
#     Then when a newly port is requested, a free port is chosen randomly,
#     then checked - with ss again - that it is free; 
#     and again until a free port is found
#     raises NoFreePort if the sytem has run out
#     """
#     
#     def __init__(self, ip, scope):
#         """
#         The IP address to watch (either 0.0.0.0 or localhost or a specific public IP)
#         """
#         self.scope = set(scope)
#         self.free = set()
# 
#     def _initialize(self):
#         """
#         """
        
