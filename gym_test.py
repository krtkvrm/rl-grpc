import gym
import pickle 

env = gym.make('CartPole-v0')
env.reset()
done = None
score = 0

def pack_for_grpc(entity):
    return pickle.dumps(entity)

def unpack_for_grpc(entity):
    return pickle.loads(entity)

# Serialized
def get_action_space():
    return list(range(env.action_space.n))

print(get_action_space())

while not done:
    a = env.action_space.sample()
    print(a)
    # state, reward, done, info = env.step(a)
    feedback = env.step(a)
    done = feedback[2]
    score += 1

print(score)
