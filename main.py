import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: py main.py [codeforces|atcoder|gym]")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "codeforces":
        import app
        app.main()
    elif mode == "atcoder":
        import atcoder
        atcoder.main()
    elif mode == "gym":
        import gym
        gym.main()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: py main.py [codeforces|atcoder|gym]")
        sys.exit(1)


if __name__ == "__main__":
    main()
