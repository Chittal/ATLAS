import boto3

client = boto3.client('bedrock-agentcore-control', region_name='us-east-2')


response = client.update_agent_runtime(
    agentRuntimeId='AtlasRoutePlanningAgent-BeOWGp2VCl',
    environmentVariables={
        'AWS_REGION': 'us-east-1',
        'AWS_ACCOUNT_ID': '499691774716',
        'AWS_ACCESS_KEY_ID': 'AKIAXIV7TML6AJS2GLWN',
        'AWS_SECRET_ACCESS_KEY': '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',
        'MODEL': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'ATLAS_APP_URL': 'https://atlas-alb-1812066565.us-east-2.elb.amazonaws.com/'
    },
    agentRuntimeArtifact={
        'containerConfiguration': {
            'containerUri': '499691774716.dkr.ecr.us-east-2.amazonaws.com/atlas:latest'
        }
    },
    networkConfiguration={"networkMode": "PUBLIC"},
    roleArn='arn:aws:iam::499691774716:role/AmazonBedrockAgentCoreSDKRuntime-us-east-2-cff9f82a16'
)

print(f"Agent Runtime updated successfully!")
print(f"Agent Runtime ARN: {response['agentRuntimeArn']}")
print(f"Status: {response['status']}")
