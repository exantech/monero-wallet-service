import redis
import json
import boto3
from threading import Thread

from models.wallet import MultisigInfo
from models.push import PushRegistration

import settings
from settings import REDIS_URL


class Listener(Thread):
    def __init__(self, channel):
        self.channel = channel
        self.type = channel.split(":")[1]
        Thread.__init__(self)

    def run(self):
        conn = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
        sub = conn.pubsub(ignore_subscribe_messages=True)
        sub.subscribe(self.channel)
        while True:
            msg = sub.get_message()
            if msg is None or 'data' not in msg: continue

            data = json.loads(msg['data'])
            data.update({"type": self.type})

            pks = [[x.source, x.multisig_source] for x in MultisigInfo.select().where(MultisigInfo.wallet_id == data['wallet_id'])]
            pks = [y for x in pks for y in x]  # flatten
            pks = list({x for x in pks if x is not None}) # unique, non null

            regs = PushRegistration\
            .select(PushRegistration.platform, PushRegistration.endpoint)\
            .distinct()\
            .where(PushRegistration.public_key << pks)

            print (data, [x.endpoint for x in regs])
            print ("---\n")

            payload = json.dumps({
                "data": data
            }, ensure_ascii=False)

            apns_common_data = {"alert": "Wallet update received"}
            apns_payload = json.dumps({"aps": apns_common_data, "custom-data": payload}, ensure_ascii=False)

            message = {
                "default": "update",
                "GCM": payload,
                "APNS": apns_payload,
                "APNS_SANDBOX": apns_payload
            }

            for reg in regs:
                mid = client.publish(
                    TargetArn = reg.endpoint,
                    Message = json.dumps(message),
                    MessageStructure = 'json'
                )
                print ("MessageId", mid)


if __name__ == "__main__":
    params = {
        "aws_access_key_id": settings.SNS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.SNS_SECRET_ACCESS_KEY,
        "region_name": settings.SNS_REGION
    }
    client = boto3.client('sns', **params)

    for channel in ("stream:wallet_info", "stream:multisig_info",
                        "stream:extra_multisig_info", "stream:new_proposal",
                        "stream:proposal_status"):
        thread = Listener(channel)
        thread.start()

    thread.join()
