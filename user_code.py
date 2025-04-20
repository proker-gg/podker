import os
import random
import sys


print("hi?", flush=True)
sys.stdout.flush()

finish = random.randrange(0, 10) > 5

# test timeouts
while True:
    # if finish:
    #     break
    continue

print("hello from user code", flush=True)
