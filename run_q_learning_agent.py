"""A script for running training and evaluating a Q-learning agent."""


from gym_simplifiedtetris.agents import QLearningAgent
from gym_simplifiedtetris.envs import SimplifiedTetrisBinaryEnv as Tetris
from gym_simplifiedtetris.helpers import eval_agent, train_q_learning


def main() -> None:
    """Train and evaluate a Q-learning agent."""
    grid_dims = (7, 4)
    env = Tetris(
        grid_dims=grid_dims,
        piece_size=3,
    )
    agent = QLearningAgent(
        grid_dims=grid_dims,
        num_pieces=env.num_pieces,
        num_actions=env.num_actions,
    )
    agent = train_q_learning(
        env=env,
        agent=agent,
        num_eval_timesteps=100,
        render=True,
    )
    eval_agent(
        agent=agent,
        env=env,
        num_episodes=30,
        render=True,
    )


if __name__ == "__main__":
    main()
