"""Examples of the environments provided by gym_simplifiedtetris.
"""

import os
import sys

sys.path.append(os.getcwd())


def run_example_1() -> None:
    """Example 1 in the README's Usage section."""
    import gym
    import gym_simplifiedtetris

    env = gym.make("simplifiedtetris-binary-20x10-4-v0")
    obs = env.reset()

    # Run 10 games of Tetris, selecting actions uniformly at random.
    episode_num = 0
    while episode_num < 10:
        env.render()

        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)

        if done:
            print(f"Episode {episode_num + 1} has terminated.")
            episode_num += 1
            obs = env.reset()

    env.close()


def run_example_2() -> None:
    """Example 2 in the README's Usage section."""
    from gym_simplifiedtetris import SimplifiedTetrisBinaryEnv as Tetris

    env = Tetris(grid_dims=(20, 10), piece_size=4)


def main() -> None:
    run_example_1()
    run_example_2()


if __name__ == "__main__":
    main()
