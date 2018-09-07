import boto3
import sys
import time

if (len(sys.argv) < 4):
    print("Required arguments: region bucket-name stack-name database-password")
    exit(1)

region = sys.argv[1]
bucketName = sys.argv[2]
stackName = sys.argv[3]
password = sys.argv[4]

def readFile(fileName, mode="r"):
    f = open(fileName, mode)
    content = f.read()
    f.close()
    return content

s3 = boto3.client('s3', region_name=region)
#s3.create_bucket(
#    Bucket=bucketName,
#    CreateBucketConfiguration = {
#        'LocationConstraint': region
#   })

cf = boto3.client('cloudformation', region_name=region)

templateBody=readFile("replen.yml")

stackId = cf.create_stack(
    StackName=stackName,
    TemplateBody=templateBody
)['StackId']


stacks=[]

while (len(stacks) == 0 or stacks[0]['StackStatus'] == 'CREATE_IN_PROGRESS'):
    time.sleep(5)
    stacks=cf.describe_stacks(
        StackName=stackName
    )['Stacks']

if (stacks[0]['StackStatus'] != 'CREATE_COMPLETE'):
    print("Create stack failed")
    exit(2)

resources=cf.describe_stack_resources(
    StackName=stackName
)['StackResources']

idByName = {}

for r in resources:
    idByName[r['LogicalResourceId']] = r['PhysicalResourceId']

rds = boto3.client('rds', region_name=region)
response = rds.create_db_cluster(
    DatabaseName='replen',
    DBClusterIdentifier=stackName,
    VpcSecurityGroupIds=[ idByName['DatabaseSecurityGroup'] ],
    DBSubnetGroupName=idByName['DatabaseSubnetGroup'],
    Engine='aurora',
    MasterUsername='replen',
    MasterUserPassword=password,
    EngineMode='serverless',
    ScalingConfiguration={
        'MinCapacity':2,
        'MaxCapacity':32,
        'SecondsUntilAutoPause':300
    }
)

clusterId=response['DBCluster']['DBClusterIdentifier']
endpoint=response['DBCluster']['Endpoint']
connectScript='connect-aurora.sh'
sqlScript='loadReplen.sql'

s3.upload_file(sqlScript, bucketName, sqlScript)
f = open(connectScript, "w")
f.write('#!/bin/bash\n')
f.write(f'mysql -u{stackName}  -p{password} -h{endpoint} {stackName}\n')
f.close()

s3.upload_file(connectScript, bucketName, connectScript)
s3.upload_file(sqlScript, bucketName, sqlScript)

time.sleep(120) #wait for database cluster to be completed

ec2Template=readFile('replen-bastion.yml')
stackId = cf.create_stack(
    StackName=stackName+"-bastion",
    TemplateBody=ec2Template,
    Capabilities=['CAPABILITY_IAM'],
    Parameters=[
        {'ParameterKey':'Database', 'ParameterValue': stackName},
        {'ParameterKey':'Username', 'ParameterValue':stackName},
        {'ParameterKey':'Password', 'ParameterValue':password},
        {'ParameterKey':'Endpoint', 'ParameterValue':response['DBCluster']['Endpoint']},
        {'ParameterKey':'SecurityGroupId', 'ParameterValue':idByName['BastionSecurityGroup']},
        {'ParameterKey':'SubnetId', 'ParameterValue':idByName['PublicSubnet1']}
    ]
)['StackId']



