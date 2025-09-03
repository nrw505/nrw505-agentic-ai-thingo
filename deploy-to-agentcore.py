#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import uuid
import string
import random
import zipfile
import tempfile
import collections
import boto3
import botocore
from pathlib import Path

# Setup for this particular competition
Knowledge_Base_1_Id = "CGM7IW6K5N"
Knowledge_Base_2_Id = "C5Z0MTKCDQ"
System_Function_1_Name = "team-PetStoreInventoryManagementFunction-uRow08ojBb6P"
System_Function_2_Name = "team-PetStoreUserManagementFunction-8yCr6nXAGKSJ"
Agent_Directory_Name = "pet_store_agent"
CodeBucketForAutomationName = "team-codebucketforautomation-znoriku8tdvl"
SolutionAccessRoleArn = (
    "arn:aws:iam::835936620626:role/team-SolutionAccessRole-IGHiqmeSFNh3"
)

# Kick start building arm64 container image
role_name = SolutionAccessRoleArn.split("/")[-1]
repository_name = "strands-agent-repo"

session = boto3.Session()
account_id = session.client("sts").get_caller_identity()["Account"]
region = session.region_name
ecr_repo = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository_name}"
ecr_uri = f"{ecr_repo}:latest"

# Create ECR repo
try:
    session.client("ecr").create_repository(repositoryName=repository_name)
    print(f"Created ECR repository {repository_name}")
except:
    pass

os.system(
    f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
)
os.system(f"docker build -t {repository_name}:latest .")
os.system(f"docker tag {repository_name}:latest {ecr_uri}")
os.system(f"docker push {ecr_uri}")

# Verify the image exists in ECR
try:
    ecr_client = boto3.client("ecr")
    response = ecr_client.describe_images(
        repositoryName=repository_name, imageIds=[{"imageTag": "latest"}]
    )
    print(f"Image verified in repository: {repository_name}")
except Exception as e:
    print(f"Error verifying image: {str(e)}")
    exit(1)


# Create or Update AgentCore Runtime
existing_runtime = None
region = boto3.Session().region_name
agent_runtime_name = "StrandsAgentCoreRuntime"
agentcore_control_client = boto3.client("bedrock-agentcore-control")

# Try to get existing agent runtime first
list_response = agentcore_control_client.list_agent_runtimes()
for runtime in list_response.get("agentRuntimes", []):
    if runtime["agentRuntimeName"] == agent_runtime_name:
        existing_runtime = runtime
        agent_runtime_id = existing_runtime["agentRuntimeId"]
        agent_runtime_arn = existing_runtime["agentRuntimeArn"]
        print(f"Found existing AgentCore Runtime ID: {agent_runtime_id}")

if existing_runtime:  # Update the existing runtim
    update_response = agentcore_control_client.update_agent_runtime(
        agentRuntimeId=agent_runtime_id,
        roleArn=SolutionAccessRoleArn,
        agentRuntimeArtifact={"containerConfiguration": {"containerUri": ecr_uri}},
        networkConfiguration={"networkMode": "PUBLIC"},
        environmentVariables={
            "AWS_DEFAULT_REGION": region,
            "KNOWLEDGE_BASE_1_ID": Knowledge_Base_1_Id,
            "KNOWLEDGE_BASE_2_ID": Knowledge_Base_2_Id,
            "SYSTEM_FUNCTION_1_NAME": System_Function_1_Name,
            "SYSTEM_FUNCTION_2_NAME": System_Function_2_Name,
        },
    )
    print(f"Updated existing AgentCore Runtime")
else:  # Create new runtime
    create_response = agentcore_control_client.create_agent_runtime(
        agentRuntimeName=agent_runtime_name,
        roleArn=SolutionAccessRoleArn,
        agentRuntimeArtifact={"containerConfiguration": {"containerUri": ecr_uri}},
        networkConfiguration={"networkMode": "PUBLIC"},
        environmentVariables={
            "AWS_DEFAULT_REGION": region,
            "KNOWLEDGE_BASE_1_ID": Knowledge_Base_1_Id,
            "KNOWLEDGE_BASE_2_ID": Knowledge_Base_2_Id,
            "SYSTEM_FUNCTION_1_NAME": System_Function_1_Name,
            "SYSTEM_FUNCTION_2_NAME": System_Function_2_Name,
        },
    )
    agent_runtime_id = create_response["agentRuntimeId"]
    agent_runtime_arn = create_response["agentRuntimeArn"]
    print(f"Created new AgentCore Runtime ID: {agent_runtime_id}")


def check_runtime_status(agent_runtime_id):
    """Check the status of the AgentCore Runtime"""
    response = agentcore_control_client.get_agent_runtime(
        agentRuntimeId=agent_runtime_id
    )
    return response["status"]


# Wait for the runtime to be ready
print("Waiting for AgentCore Runtime to be ready...")
runtime_status = check_runtime_status(agent_runtime_id)
while runtime_status not in [
    "READY",
    "CREATE_FAILED",
    "DELETE_FAILED",
    "UPDATE_FAILED",
]:
    print(f"Runtime status: {runtime_status}")
    time.sleep(10)
    runtime_status = check_runtime_status(agent_runtime_id)
print(f"Runtime status: {runtime_status}")

# Create a client for the AgentCore data plane
agentcore_client = boto3.client("bedrock-agentcore")

# Test the AgentCore Runtime with a sample query
try:
    invoke_response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=agent_runtime_arn,
        qualifier="DEFAULT",
        traceId=str(uuid.uuid4()),
        contentType="application/json",
        # payload=json.dumps({"prompt": "A new user is asking about the price of Doggy Delights"})
        payload=json.dumps(
            {
                "prompt": """CustomerName: Ahmed
CustomerRequest: I'd like to order 3 Meow Munchies and 2 Bark Bites for my pets.
        """
            }
        ),
    )

    # Process the response
    if "text/event-stream" in invoke_response.get("contentType", ""):
        content = []
        for line in invoke_response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    content.append(line)
        response_text = "\n".join(content)
    else:
        events = []
        for event in invoke_response.get("response", []):
            events.append(event)

        # Combine all events to fix truncation
        combined_content = ""
        for event in events:
            combined_content += event.decode("utf-8")

        response_text = json.loads(combined_content)
    print("Agent Response:")
    print(response_text)
except Exception as e:
    print(f"Error invoking AgentCore Runtime: {str(e)}")
    exit(1)
