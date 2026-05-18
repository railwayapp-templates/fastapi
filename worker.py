from app.tasks import celery

celery.worker_main()