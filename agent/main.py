"""
CLI
"""


def run_cli(agent):
    """Run the CLI."""
    print("Welcome to the Strands CLI! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        response = agent(user_input)
        print(f"Agent: {response}")


if __name__ == "__main__":
    from agent import agent as configured_agent

    run_cli(configured_agent)
