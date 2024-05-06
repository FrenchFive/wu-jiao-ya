import os
import random
import time
import datetime
from alive_progress import alive_bar
import pytz

while True:
    with open("time.txt", 'r', encoding='utf-8') as file:
        run_time = file.readline()
    run_time = float(run_time)
    
    waiting = int((run_time - time.time()))
    wait = True
    if waiting <= 0:
        wait = False
    
    timezone = pytz.timezone('Europe/Paris')
    print(f'WAITING FOR :: {waiting} seconds - {str(datetime.timedelta(seconds=waiting))} - PUBLISHING DATE :: {datetime.datetime.fromtimestamp(run_time, tz=timezone).strftime("%d-%m-%Y %H:%M:%S")}')
    mult = 1
    with alive_bar(int(waiting*mult), spinner_length=6) as bar:
        for i in range(waiting):
            for i in range(mult):
                bar()
                time.sleep(1/mult)
            

    print(f'// RUNNING :: {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")}')

    # Launch the "main.py" script
    python_file = "G:/Chan/Documents/zWuKongBai/main.py"
    os.system(f"python {python_file}")

    with open("time.txt", 'w', encoding='utf-8') as file:
        multiplier = 60 * 60 * 24
        next_time = time.time() + random.randint((1.75 * multiplier), (2.25 * multiplier))
        file.write(str(next_time))