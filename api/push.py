from flask import jsonify, request
import boto3
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO)

from api import app
from models.push import PushRegistration
from .auth import authentication, wallet_required, Session
from .exceptions import APIError
from .utils import validate_json_params
import settings


@app.route("/api/v1/push/register", methods=["POST"])
@validate_json_params("platform", "device_uid", "token")
@authentication
def PushRegisterEndpoint(session, data):
# def PushRegisterEndpoint(data):
#    session = Session(public_key="test-key", id = "test_session")

    platform_arn = settings.SNS_PLATFORM_ARNS.get(data['platform'])
    # topic_arn = settings.SNS_TOPIC_ARNS.get(spec.locale)

    if not platform_arn:
        return

    params = {
        "aws_access_key_id": settings.SNS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.SNS_SECRET_ACCESS_KEY,
        "region_name": settings.SNS_REGION
    }

    try:
        spec = PushRegistration.select().where(
            PushRegistration.platform == data['platform'],
            PushRegistration.device_uid == data['device_uid'],
            PushRegistration.public_key == session.public_key
        ).first()

        if spec and spec.token == data['token']:
            return jsonify({"status": "ok", "endpoint": spec.endpoint})

        else:
            if not spec or (spec.token != data['token']):
                sns = boto3.client('sns', **params)

                endpoint = sns.create_platform_endpoint(
                    PlatformApplicationArn = platform_arn,
                    Token = data['token'],
                    CustomUserData = data['device_uid']
                )['EndpointArn']

            else:
                endpoint = spec.endpoint

            if not spec:
                spec = PushRegistration.create(
                    platform = data['platform'],
                    device_uid = data['device_uid'],
                    token = data['token'],
                    public_key = session.public_key,
                    endpoint = endpoint,
                    locale = "en"
                )

            else:
                spec.token = data['token']
                spec.endpoint = endpoint
                spec.timestamp = datetime.now()
                spec.save()

        return jsonify({"status": "ok", "endpoint": spec.endpoint})

        # previous_subscription = spec.subscription

        # if previous_subscription:
        #     conn.unsubscribe(previous_subscription)

        # subscription = conn.subscribe(
        #     topic_arn,
        #     "application",
        #     endpoint['CreatePlatformEndpointResponse']['CreatePlatformEndpointResult']['EndpointArn']
        # )
        # spec.subscription = subscription['SubscribeResponse']['SubscribeResult']['SubscriptionArn']
        # spec.save(update_fields=['subscription', ])

    except Exception as e:
        logging.exception("Push register error")
        raise APIError(str(e), status_code=500)


@app.route("/api/v1/push/deregister", methods=["POST"])
@validate_json_params("platform", "device_uid")
@authentication
def PushDeregisterEndpoint(session, data):
    pass
