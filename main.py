from pymongo import MongoClient
from paho.mqtt import client as mqtt_client
from datetime import datetime
import random
import json
import environ
import os
import logging

ENVIRONMENT_FILE_LOCATION = os.environ.get('ENVIRONMENT_FILE_LOCATION', None)

# Inicia environ
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env()

# Variáveis globais
DEBUG = env('DEBUG')
SENSOR_COLLECTION_NAME = env('MONGODB_MQTT_COLLECTION')
MQTT_BROKER_TOPIC = env('MQTT_BROKER_TOPIC')
LOG_LEVEL = logging.DEBUG if env('DEBUG') else logging.INFO

logging.basicConfig(level=LOG_LEVEL)

def get_database():
    collection_name = SENSOR_COLLECTION_NAME
    
    client = MongoClient(env('MONGODB_CONNECTION_STRING'))
    return client[collection_name]

def store_data(db_collection, data: dict):
    # Formata timestamp antes de inserir
    formatted_data = {
        'timestamp': datetime.strptime(data['timestamp'],'%Y-%m-%d %H:%M:%S'),
        'sensors': data['sensors']
    }
    

    inserted_id = db_collection.insert_one(formatted_data).inserted_id
    logging.info(f"Document stored with id {inserted_id}")

def connect_mqtt_broker():
    broker = env('MQTT_BROKER_URL')
    port = env.int('MQTT_BROKER_PORT')
    topic = MQTT_BROKER_TOPIC
    client_id = f'python-mqtt-{random.randint(0,1000)}'
    username =  env('MQTT_BROKER_USERNAME')
    password = env('MQTT_BROKER_PASSWORD') 

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.info(f"Failed to connect, return code {rc}")

    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client, topic: str, db_collection):
    def on_message(client, userdata, msg):
        # Mensagem decodificada
        msg_dict = json.loads(msg.payload.decode())

        # Armazena o dicionário no banco de dados
        store_data(db_collection, msg_dict)

    client.subscribe(topic)
    client.on_message = on_message
    #logging.info(f"subscribed to topic {topic}")

def setup_and_run():
    try:
        # Busca a conexao ao banco
        logging.info("Connecting to database...")
        dbname = get_database()

        # Inicia a collection
        logging.info("Starting collection...")
        collection = dbname[SENSOR_COLLECTION_NAME]

        # Setup do client MQTT
        logging.info("Connecting to broker...")
        mqtt_client = connect_mqtt_broker()

        # Inscreve no tópico 'sensors' e escuta o broker para sempre
        subscribe(mqtt_client, MQTT_BROKER_TOPIC, collection)
        mqtt_client.loop_forever()
    except Exception as e:
        logging.info(str(e))

#if __name__ == "__main__":
setup_and_run()
    

    
