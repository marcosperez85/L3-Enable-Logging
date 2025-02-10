#!/usr/bin/env python
# coding: utf-8

# # Lesson 3: Enable Logging
# La posibilidad de habilitar logging globalmente en Bedrock es con propósitos de auditoria y cumplimiento de normativas
# para saber todo lo que está ocurriendo detrás de escena con los mensajes que entran y salen del LLM.
# Esto también nos va a sevir para monitorear condiciones de error en nuestro código.

# ### Import all needed packages
import boto3
import json
import os
from helpers.CloudWatchHelper import CloudWatch_Helper

# Recordar que Cloudwatch es un servicio de AWS que se encarga de crear logs y métricas del estado
# de salud de los servicios que utilizamos. Desde luego los logs los podemos ver en la consola de AWS también.

session = boto3.Session(profile_name = "AdministratorAccess-376129873205")

# Estamos creando un cliente de Bedrock pero no un cliente de Bedrock Runtime porque no vamos a usar esto para
# generar texto sino para evaluar el servicio mismo de Bedrock (para crear los logs)
bedrock = session.client('bedrock', region_name="us-east-1")

cloudwatch = CloudWatch_Helper()

# Dentro de CloudWatch existen grupos de logs y el siguiente código lo que hace es crear un grupo para nuestros registros.
# Tener en cuenta que la ubicación que se ve abajo fue sugerida por el instructor del tutorial y la misma tiene seteado
# permisos en la # cuenta de AWS de Deeplearning por lo que, sea cual sea nuestra ubicación de logs, tenemos que setearle
# permisos también. # Estos permisos son: IAM. Mirando el JSON de permisos se ve que tiene los keys:
# "CreateLogStreams" y "PutLogEvents". # Luego el resource que tiene permiso para esto es Amazon Bedrock model invokations.
# También tienen seteado un Trust Policy que puede ser asumida por  el servicio de Bedrock

# String con la ubicación de los logs
log_group_name = '/my/amazon/bedrock/logs'

# Invoco al servicio de CloudWatch para que genere dicha ubicación
cloudwatch.create_log_group(log_group_name)

# Todo lo anterior se puede hacer igualmente desde la consola de AWS.

loggingConfig = {
    'cloudWatchConfig': {
        'logGroupName': log_group_name,
        'roleArn': os.environ['LOGGINGROLEARN'],
        'largeDataDeliveryS3Config': {
            'bucketName': os.environ['LOGGINGBUCKETNAME'],
            'keyPrefix': 'amazon_bedrock_large_data_delivery',
        }
    },
    's3Config': {
        'bucketName': os.environ['LOGGINGBUCKETNAME'],
        'keyPrefix': 'amazon_bedrock_logs',
    },
    'textDataDeliveryEnabled': True,
}

bedrock.put_model_invocation_logging_configuration(loggingConfig=loggingConfig)
bedrock.get_model_invocation_logging_configuration()

# Ahora sí vamos a crear un cliente del runtime de Bedrock
bedrock_runtime = boto3.session('bedrock-runtime', region_name="us-east-1")

prompt = "Write an article about the fictional planet Foobar."

kwargs = {
    "modelId": "amazon.titan-text-lite-v1",
    "contentType": "application/json",
    "accept": "*/*",
    "body": json.dumps(
        {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 512,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
    )
}

response = bedrock_runtime.invoke_model(**kwargs)
response_body = json.loads(response.get('body').read())
generation = response_body['results'][0]['outputText']
print(generation)

cloudwatch.print_recent_logs(log_group_name)

# Mostrar un link para ir a revisar los logs generados en la consola de AWS
aws_url = os.environ.get('AWS_CONSOLE_URL', 'https://aws.amazon.com/console/')
print(f"GO TO AWS CONSOLE: {aws_url}")
