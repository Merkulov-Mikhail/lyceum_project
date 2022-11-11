import time
import os


def ex(dr, cnt=0):
    print(dr)
    if cnt == 0:
        return
    try:
        for i in os.listdir(dr):
            if os.path.isdir(dr + "/" + i):
                ex(dr + "/" + i, cnt=cnt - 1)
    except PermissionError:
        print("ERROR")
        return


a = time.time()
ex("C:/Users", cnt=2)
print(a - time.time())