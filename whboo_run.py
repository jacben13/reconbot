import schedule
import time
import os

from reconbot.tasks import esi_notification_task
from reconbot.notifiers.caching import CachingNotifier
from reconbot.notifiers.discordwebhook import DiscordWebhookNotifier
from reconbot.notifiers.splitter import SplitterNotifier
from reconbot.apiqueue import ApiQueue
from reconbot.esi import ESI
from reconbot.sso import SSO
from dotenv import load_dotenv

load_dotenv()

notification_caching_timer  = 5
attack_notifs_url           = os.getenv("ATTACK_NOTIFS_WEBHOOK_URL")
infra_notifs_url            = os.getenv("INFRA_NOTIFS_WEBHOOK_URL")
sso_app_client_id           = os.getenv("SSO_APP_CLIENT_ID")
sso_app_secret_key          = os.getenv("SSO_APP_SECRET_KEY")
character_one_name          = os.getenv("CHARACTER_ONE_NAME")
character_one_id            = int(os.getenv("CHARACTER_ONE_ID"))
character_one_token         = os.getenv("CHARACTER_ONE_TOKEN")
character_two_name          = os.getenv("CHARACTER_TWO_NAME")
character_two_id            = int(os.getenv("CHARACTER_TWO_ID"))
character_two_token         = os.getenv("CHARACTER_TWO_TOKEN")


discord_webhooks = {
                    'attack_webhook' : attack_notifs_url,
                    'infra_webhook' : infra_notifs_url
                   }

sso_app = {
    'client_id': sso_app_client_id,
    'secret_key': sso_app_secret_key
}

eve_apis = {
    'attack-notifications-group': {
        'notifications': {
            'whitelist': [
                #'AllWarDeclaredMsg',
                #'DeclareWar',
                #'AllWarInvalidatedMsg',
                #'AllyJoinedWarAggressorMsg',
                #'CorpWarDeclaredMsg',
                #'OwnershipTransferred',
                #'MoonminingExtractionStarted',
                #'MoonminingExtractionCancelled',
                #'MoonminingExtractionFinished',
                'SovStructureDestroyed',
                'SovStructureReinforced',
                'StructureUnderAttack',
                #'OwnershipTransferred',
                #'StructureOnline',
                #'StructureFuelAlert',
                #'StructureAnchoring',
                'StructureServicesOffline',
                'StructureLostShields',
                'StructureLostArmor',
                'TowerAlertMsg',
                #'StationServiceEnabled',
                #'StationServiceDisabled',
                #'SovAllClaimAquiredMsg',
                #'SovStationEnteredFreeport',
                #'SovAllClaimLostMsg',
                'SovStructureSelfDestructRequested',
                'SovStructureSelfDestructFinished',
                'StationConquerMsg',
            ],
        },
        'characters': {
            character_one_name: {
                'character_name': character_one_name,
                'character_id': character_one_id,
                'refresh_token': character_one_token
            },
        },
        'notifier': CachingNotifier(DiscordWebhookNotifier(attack_notifs_url), duration=7200)
    },
    'infra-notifications-group': {
        'notifications': {
            'whitelist': [
                #'AllWarDeclaredMsg',
                #'DeclareWar',
                #'AllWarInvalidatedMsg',
                #'AllyJoinedWarAggressorMsg',
                #'CorpWarDeclaredMsg',
                'OwnershipTransferred',
                'MoonminingExtractionStarted',
                'MoonminingExtractionCancelled',
                'MoonminingExtractionFinished',
                #'SovStructureDestroyed',
                #'SovStructureReinforced',
                #'StructureUnderAttack',
                'OwnershipTransferred',
                'StructureOnline',
                'StructureFuelAlert',
                'StructureAnchoring',
                'StructureServicesOffline',
                #'StructureLostShields',
                #'StructureLostArmor',
                'TowerAlertMsg',
                'StationServiceEnabled',
                'StationServiceDisabled',
                'SovAllClaimAquiredMsg',
                'SovStationEnteredFreeport',
                'SovAllClaimLostMsg',
                'SovStructureSelfDestructRequested',
                'SovStructureSelfDestructFinished',
                'StationConquerMsg',
            ],
        },
        'characters': {
            character_one_name: {
                'character_name': character_two_name,
                'character_id': character_two_id,
                'refresh_token': character_two_token
            },
        },
        'notifier': CachingNotifier(DiscordWebhookNotifier(infra_notifs_url), duration=7200)
    }
}


def api_to_sso(api):
    return SSO(
        sso_app['client_id'],
        sso_app['secret_key'],
        api['refresh_token'],
        api['character_id']
    )

api_queue_attack = ApiQueue(list(map(api_to_sso, eve_apis['attack-notifications-group']['characters'].values())))
api_queue_infra = ApiQueue(list(map(api_to_sso, eve_apis['infra-notifications-group']['characters'].values())))

def notifications_job_attack():
    esi_notification_task(
        eve_apis['attack-notifications-group']['notifications'],
        api_queue_attack,
        'discord',
        eve_apis['attack-notifications-group']['notifier'],
    )

def notifications_job_infra():
    esi_notification_task(
        eve_apis['infra-notifications-group']['notifications'],
        api_queue_infra,
        'discord',
        eve_apis['infra-notifications-group']['notifier'],
    )

def run_and_schedule(characters, notifications_job):
    notifications_job()
    schedule.every(notification_caching_timer/len(characters)).minutes.do(notifications_job)

run_and_schedule(eve_apis['attack-notifications-group']['characters'], notifications_job_attack)
run_and_schedule(eve_apis['infra-notifications-group']['characters'], notifications_job_infra)

while True:
    schedule.run_pending()
    time.sleep(1)
