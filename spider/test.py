import multiprocessing
import time


q = multiprocessing.Queue()

def p1(q:multiprocessing.Queue):
    a = q.get()
    print(a)

def p2(q:multiprocessing.Queue):
    time.sleep(5)
    for i in range(5):
        print("Sending hi from p2")
        q.put("hi from p2")
        print("Sent hi from p2")

for i in range(5):
    p = multiprocessing.Process(target=p1, args=(q,))
    p.start()

p2 = multiprocessing.Process(target=p2, args=(q,))
p2.start()