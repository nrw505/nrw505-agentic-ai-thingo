"Python file to run a CLI for testing"

import pet_store_agent


def run_cli():
    "Run a CLI"
    try:
        while True:
            user_input = ""
            line_input = input("> ")
            while line_input:
                user_input += line_input
                line_input = input("> ")
            if len(user_input) > 0:
                response = pet_store_agent.process_request(user_input)
                print(f"Response:\n{response}\n")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")


if __name__ == "__main__":
    run_cli()
