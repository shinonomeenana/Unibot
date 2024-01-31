from modules.sk import eventtrack, getranks
from apscheduler.schedulers.blocking import BlockingScheduler


scheduler = BlockingScheduler()
scheduler.add_job(eventtrack, 'cron', second=0, id='chafang')
scheduler.add_job(getranks, 'cron', second=5)
scheduler.start()