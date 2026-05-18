from celery import Celery
import time

celery = Celery(
    __name__,
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)
@celery.task
def send_email_task(email):
    print(f"Sending email to {email}...")
    time.sleep(5)  # Simulate delay
    print(f"Email sent to {email} 🎉")