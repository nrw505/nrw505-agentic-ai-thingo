from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent import agent as configured_agent

app = BedrockAgentCoreApp()


@app.entrypoint
def handler(payload):
    """AgentCore handler function"""
    prompt = payload.get(
        "prompt", "A new user is asking about the price of Doggy Delights?"
    )
    return str(configured_agent(prompt))


if __name__ == "__main__":
    app.run()
