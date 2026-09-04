from jhalcode.config import JhalConfig
from jhalcode.agent import JhalAgent


def main():
    cfg = JhalConfig()
    print(JhalAgent(cfg).run("List files in current folder and summarize."))


if __name__ == "__main__":
    main()
