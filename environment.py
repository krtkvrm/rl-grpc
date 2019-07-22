import grpc
import gym
import pickle 
import sys
import os
import requests
import json

# from .interface import EvalAI_Interface

from concurrent import futures
import time

import evaluation_pb2
import evaluation_pb2_grpc

BODY = os.environ.get("BODY")
print(BODY)
BODY = BODY.replace("'", '"')
print(json.loads(BODY))
BODY = json.loads(BODY)
challenge_pk = BODY["challenge_pk"]
phase_pk = BODY["phase_pk"]
submission_pk = BODY["submission_pk"]



#####


challenge_pk=1
# phase_pk=1
# submission_pk=10
####

def pack_for_grpc(entity):
    return pickle.dumps(entity)

def unpack_for_grpc(entity):
    return pickle.loads(entity)

# Serialized
def get_action_space(env):
    return list(range(env.action_space.n))

def finalize(env):
    # api.update_submission_status("finished")
    print("Final Score: {0}".format(env.score))
    print("Stopping Evaluator")
    submission_data = {
        "submission_status": "finished",
        "submission": submission_pk,
    }
    # api.update_submission_status(submission_data, challenge_pk)
    submission_data = {
        "challenge_phase": phase_pk,
        "submission":submission_pk,
        "stdout": "ABC",
        "stderr": "XYZ",
        "submission_status": "FINISHED",
        "result": json.dumps([{'split': 'split1', 'show_to_participant': True, 'accuracies': {'score': env.score}}])
    }
    print("SUBMISSION DATA: {0}".format(submission_data))
    api.update_submission_data(submission_data, challenge_pk)
    exit(0)

# logger = logging.getLogger(__name__)


URLS = {
    "get_message_from_sqs_queue": "/api/jobs/challenge/queues/{}/",
    "delete_message_from_sqs_queue": "/api/jobs/queues/{}/receipt/{}/",
    "get_submission_by_pk": "/api/jobs/submission/{}",
    "get_challenge_phases_by_challenge_pk": "/api/challenges/{}/phases/",
    "get_challenge_by_queue_name": "/api/challenges/challenge/queues/{}/",
    "get_challenge_phase_by_pk": "/api/challenges/challenge/{}/challenge_phase/{}",
    "update_submission_data": "/api/jobs/challenge/{}/update_submission/",
}


class EvalAI_Interface:

    def __init__(
            self,
            AUTH_TOKEN,
            DJANGO_SERVER,
            DJANGO_SERVER_PORT,
            QUEUE_NAME,

    ):
        self.AUTH_TOKEN = AUTH_TOKEN
        self.DJANGO_SERVER = DJANGO_SERVER
        self.DJANGO_SERVER_PORT = DJANGO_SERVER_PORT
        self.QUEUE_NAME = QUEUE_NAME

    def get_request_headers(self):
        headers = {"Authorization": "Token {}".format(self.AUTH_TOKEN)}
        return headers

    def make_request(self, url, method, data=None):
        headers = self.get_request_headers()
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=200
            )
            # response.raise_for_status()
        except requests.exceptions.RequestException:
            # logger.info(
            #     "The worker is not able to establish connection with EvalAI"
            # )
            print("The worker is not able to establish connection with EvalAI")
            raise
        print(response.text)
        return response.json()

    def return_url_per_environment(self, url):
        base_url = "{0}:{1}".format(self.DJANGO_SERVER, self.DJANGO_SERVER_PORT)
        url = "{0}{1}".format(base_url, url)
        return url

    def get_message_from_sqs_queue(self):
        url = URLS.get("get_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def delete_message_from_sqs_queue(self, receipt_handle):
        print(receipt_handle)
        url = URLS.get("delete_message_from_sqs_queue").format(
            self.QUEUE_NAME, "A"
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "POST", data={
            "receipt_handle": receipt_handle
        })  # noqa
        return response

    def get_submission_by_pk(self, submission_pk):
        url = URLS.get("get_submission_by_pk").format(submission_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_phases_by_challenge_pk(self, challenge_pk):
        url = URLS.get("get_challenge_phases_by_challenge_pk").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_by_queue_name(self):
        url = URLS.get("get_challenge_by_queue_name").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_phase_by_pk(self, challenge_pk, challenge_phase_pk):
        url = URLS.get("get_challenge_phase_by_pk").format(
            challenge_pk, challenge_phase_pk
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def update_submission_data(self, data, challenge_pk):
        url = URLS.get("update_submission_data").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_submission_status(self, data, challenge_pk):
        url = URLS.get("update_submission_data").format(challenge_pk)
        url = self.return_url_per_environment(url)
        print("ABC")
        response = self.make_request(url, "PATCH", data=data)
        print("XYZ")
        return response


class evaluator_environment:
    def __init__(self, environment='CartPole-v0'):
        self.score = 0
        self.feedback = None
        self.env = gym.make(environment)
        self.env.reset()

    def get_action_space(self):
        return list(range(self.env.action_space.n))

    def next_score(self):
        self.score += 1

env = evaluator_environment()
api = EvalAI_Interface(
    AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "97cd1116ed461b25154f191392cd36cd318f3cd6"),
    DJANGO_SERVER = os.environ.get("DJANGO_SERVER", "http://localhost"),
    DJANGO_SERVER_PORT = os.environ.get("DJANGO_SERVER_PORT", "8000"),
    QUEUE_NAME = os.environ.get("QUEUE_NAME", ""),
)

class Environment(evaluation_pb2_grpc.EnvironmentServicer):

    def get_action_space(self, request, context):
        message = pack_for_grpc(env.get_action_space())
        return evaluation_pb2.Package(SerializedEntity=message)

    def act_on_environment(self, request, context):
        if not env.feedback or not env.feedback[2]:
            action = unpack_for_grpc(request.SerializedEntity)
            env.next_score()
            env.feedback = env.env.step(action)
        if env.feedback[2]:
            finalize(env)
        return evaluation_pb2.Package(SerializedEntity=pack_for_grpc({
            "feedback": env.feedback,
            "current_score": env.score,
        }))


# finalize(400)

# NOW COMMENT
server = grpc.server(futures.ThreadPoolExecutor(max_workers = 10))
evaluation_pb2_grpc.add_EnvironmentServicer_to_server(Environment(), server)


print('Starting server. Listening on port 8080.')
server.add_insecure_port('[::]:8080')
server.start()
# time.sleep(10)
try:
    while True:
        time.sleep(4)
except KeyboardInterrupt:
    server.stop(0)
