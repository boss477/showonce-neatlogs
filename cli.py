import argparse
from showonce.runner import demo

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["demo"]); args = parser.parse_args()
    print(demo() if args.command == "demo" else "")

