import sys, traceback, datetime, os

from reconbot.notificationprinters.esi.discord import Discord as ESIDiscord
from reconbot.esi import ESI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def esi_notification_task(notification_options, api_queue, printer, notifier):
    MAX_NOTIFICATION_AGE_IN_SECONDS = int(os.getenv("MAX_NOTIFICATION_AGE_IN_SECONDS"))
    
    try:
        sso = api_queue.get()
        print(f'{datetime.now().strftime("%H:%M:%S")}: Notifications query for character with id {sso.character_id}')

        esi = ESI(sso)

        notifications = esi.get_new_notifications(max_age=MAX_NOTIFICATION_AGE_IN_SECONDS)

        if 'whitelist' in notification_options and type(notification_options['whitelist']) is list:
            notifications = [notification for notification in notifications if notification['type'] in notification_options['whitelist']]
        
        printer = ESIDiscord(esi)        

        messages = map(lambda text: printer.transform(text), notifications)

        for message in messages:
            notifier.notify(message)

    except Exception as e:
        notify_exception("esi_notification_task", e)

def notify_exception(location, exception):
    print('[%s] Exception in %s' % (datetime.now(), location))
    print('-' * 60)
    traceback.print_exc(file=sys.stdout)
    print(exception)
    print('-' * 60)
