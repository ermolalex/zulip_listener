import threading
import time
from functools import wraps

def async_exec(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
        return thr  # returns the thread object for optional joining
    return wrapper

@async_exec
def task(name, foo):
    try:
        print(f"Thread {name}: starting...")
        time.sleep(2) # Simulate I/O operation
        print(f"Thread {name}: finishing.")
        a = 1/foo
    except Exception as e:
        print(e)

t1 = task("A", 0)
t2 = task("B", 1)
# # Create a thread A
# a_thread = threading.Thread(target=task, args=("A", 1))
# a_thread.start()
#
# # Create a thread B
# b_thread = threading.Thread(target=task, args=("B", 2))
# b_thread.start()
#

print("Main thread: doing other work.")

# Wait for the thread to finish
t1.join()
t2.join()

print("Main thread: all done.")