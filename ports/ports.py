import socket

# http://stackoverflow.com/questions/2838244/get-open-tcp-port-in-python/2838309#2838309
def free_port():
    "return a free TCP port"
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
    

