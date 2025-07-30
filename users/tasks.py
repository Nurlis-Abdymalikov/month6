from celery import shared_task
import time
import random

@shared_task
def send_opt_email(user_email, code):
    print("Sending...")
    time.sleep(20)
    print("Email sent")

@shared_task
def send_daily_report():
    print("sending daily report ....")
    time.sleep(50)
    print("daily report sent")

@shared_task
def generate_random_number():
    number = random.randint(1000, 9999)
    print(f"Generated number: {number}")
    with open("random_numbers.txt", "a") as f:
        f.write(f"{number}\n")

@shared_task
def clear_old_logs():
    import os

    if os.path.exists("random_numbers.txt"):
        with open("random_numbers.txt", "w") as f:
            f.write("")
        print("Old logs cleared")
    else:
        print("Log file does not exist.")