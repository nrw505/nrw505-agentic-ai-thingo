
FROM --platform=linux/arm64 public.ecr.aws/docker/library/python:3.12-slim-bookworm

WORKDIR /app

# Copy requirements and install dependencies
COPY pet_store_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install bedrock-agentcore
RUN pip install aws-opentelemetry-distro

# Copy agent code and tools
COPY pet_store_agent/*.py ./
COPY pet_store_agent/*.txt ./

# Set default AWS region
ENV AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}

# Set agent resources variables
ENV KNOWLEDGE_BASE_1_ID=${KNOWLEDGE_BASE_1_ID}
ENV KNOWLEDGE_BASE_2_ID=${KNOWLEDGE_BASE_2_ID}
ENV SYSTEM_FUNCTION_1_NAME=${SYSTEM_FUNCTION_1_NAME}
ENV SYSTEM_FUNCTION_2_NAME=${SYSTEM_FUNCTION_2_NAME}

# OpenTelemetry Configuration for AWS CloudWatch GenAI Observability
ENV OTEL_PYTHON_DISTRO=aws_distro
ENV OTEL_PYTHON_CONFIGURATOR=aws_configurator
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
ENV OTEL_TRACES_EXPORTER=otlp
ENV OTEL_EXPORTER_OTLP_LOGS_HEADERS=x-aws-log-group=agents/strands-agent-logs,x-aws-log-stream=default,x-aws-metric-namespace=agents
ENV OTEL_RESOURCE_ATTRIBUTES=service.name=strands-agent
ENV AGENT_OBSERVABILITY_ENABLED=true

# Expose the port that AgentCore Runtime expects
EXPOSE 8080

# Run the agent
CMD ["opentelemetry-instrument", "python", "agentcore_entrypoint.py"]
