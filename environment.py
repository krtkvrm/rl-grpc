import grpc
import gym
import pickle 
import sys
import os
import requests
import json

from concurrent import futures
import time

import evaluation_pb2
import evaluation_pb2_grpc

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
    exit(0)

class EvalAI_Communication:

    def __init__(
            self,
            AUTH_TOKEN,
            DJANGO_SERVER,
            DJANGO_SERVER_PORT,
            CHALLENGE_PK,

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
            response = requests.request(method=method, url=url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        return response.json()
    
    def return_url_per_environment(self, url):
        base_url = "http://{0}:{1}".format(self.DJANGO_SERVER, self.DJANGO_SERVER_PORT)
        url = "{0}{1}".format(base_url, url)
        return url

    def update_submission_data(self, data):
        url = "/api/jobs/challenge/{}/update_submission/".format(self.CHALLENGE_PK)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_submission_status(self, data):
        url = "/api/jobs/challenge/{}/update_submission/".format(self.CHALLENGE_PK)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PATCH", data=data)
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
# api = EvalAI_Communication(
#     AUTH_TOKEN = os.environ.get("AUTH_TOKEN"),
#     DJANGO_SERVER = os.environ.get("DJANGO_SERVER", "localhost"),
#     DJANGO_SERVER_PORT = os.environ.get("DJANGO_SERVER_PORT", "8000"),
#     CHALLENGE_PK = os.environ.get("CHALLENGE_PK", "1"),
#     SUBMISSION_PK = os.environ.get("SUBMISSION_PK", "1"),
# )

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

server = grpc.server(futures.ThreadPoolExecutor(max_workers = 10))
evaluation_pb2_grpc.add_EnvironmentServicer_to_server(Environment(), server)

BODY = os.environ.get("BODY")
print(BODY)
BODY = BODY.replace("'", '"')
print(json.loads(BODY))


print('Starting server. Listening on port 8080.')
server.add_insecure_port('[::]:8080')
server.start()
# time.sleep(10)
try:
    while True:
        time.sleep(4)
except KeyboardInterrupt:
    server.stop(0)
