import grpc
import evaluation_pb2
import evaluation_pb2_grpc
import gym
import pickle


import time


time.sleep(60)

channel = grpc.insecure_channel(
    'localhost:8080',)

stub = evaluation_pb2_grpc.EnvironmentStub(channel)

def pack_for_grpc(entity):
    return pickle.dumps(entity)

def unpack_for_grpc(entity):
    return pickle.loads(entity)

done = None

while not done:
    base = unpack_for_grpc(
        stub.act_on_environment(evaluation_pb2.Package(SerializedEntity=pack_for_grpc(1))).SerializedEntity
    )
    time.sleep(1)
    done = base["feedback"][2]
    print(base["feedback"])
    print(done)


# a = stub.act_on_environment(evaluation_pb2.Package(SerializedEntity=pack_for_grpc("ABC")))

print(base)
# action_space = base.get("action_space")
# environment = base.get("environment")
# print(environment)

# feedback = unpack_for_grpc(
#     stub.get_action_space(evaluation_pb2.Package(SerializedEntity="1".encode()))
# )


# while not done:
#     feedback = stub.
