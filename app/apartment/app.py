from flask import Flask, jsonify, request
from bson import ObjectId, json_util
from pymongo import MongoClient
from dotenv import load_dotenv

import os
import pika

load_dotenv()

db_url = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

connection_params = pika.ConnectionParameters('rabbitmq', port=5672)
queue_name = 'main_message_queue'

client = MongoClient(db_url)
database_name = "apartment_db"


apartments_collection = "apartments"


def get_collection(collection_name):
    return client[database_name][collection_name]


@app.route('/')
def hello():
   return "Hello from apartments microservice"


@app.route('/get', methods=['GET'])
def get_single_apartment():
    apartment_id = request.args.get('id')

    if not apartment_id:
        return jsonify({"error": "Missing apartment id"}), 400
    
    result = get_collection(apartments_collection).find_one({"_id" : ObjectId(apartment_id)})
    return json_util.dumps(result)


# Endpoint for adding a new apartment
@app.route('/add', methods=['POST'])
def add_apartment():
    name = request.args.get('name')
    address = request.args.get('address')
    noiselevel = request.args.get('noiselevel')
    floor = request.args.get('floor')

    # Validate the presence of required parameters
    if not all([name, address, noiselevel, floor]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        noiselevel = int(noiselevel)
        floor = int(floor)
    except ValueError:
        floor = None
    

    apartment_data = create_apartment(name, address, noiselevel, floor)
    return insert_apartment(apartment_data)


# Endpoint for removing existing apartment
@app.route('/remove', methods=['POST'])
def remove_apartment():
    apartment_id = request.args.get('id')

    if apartment_id is None:
         return jsonify({"error": "Missing apartment_id"}), 400

    return delete_apartment(apartment_id)


# Endpoint to list all apartments
@app.route('/list', methods=['GET'])
def list_apartments():
    # Retrieve all apartments from the collection
    apartments = get_collection(apartments_collection).find()

    try:
        # Check if the Apartment collection is empty
        if apartments.count_documents({}) == 0:
            # Initialize the list of apartments
            apartment1 = create_apartment("Apartment1", 200, 2, "2024-01-01", "2024-01-07")
            apartment2 = create_apartment("Apartment2", 500, 4, "2024-01-03", "2024-01-06")

            insert_apartment(apartment1)
            insert_apartment(apartment2)

            return jsonify({'message': 'Apartments initialized successfully'})

        apartments_json = json_util.dumps(apartments)

        return jsonify(apartments_json)

    except Exception as e:
        return jsonify({'error': str(e)})


def start_producer(message, operation_name):
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        operation_message = {
            "operation": operation_name,
            "apartment": message
        }

        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=json_util.dumps(operation_message))
        connection.close()

    except pika.exceptions.AMQPError as e:
        print(f"Error while producing message: {e}")


def create_apartment(name, address, noiselevel, floor):
    return {
        "_id": ObjectId(),
        "address": address,
        "name": name,
        "noiselevel": noiselevel,
        "floor": floor
    }


def get_inserted_result(insert_result):
    response_data = {
        # "acknowledged": insert_result.acknowledged,
        "inserted_id": str(insert_result.inserted_id)  
    }

    return jsonify(response_data)


def insert_apartment(apartment_data):
    collection = get_collection(apartments_collection)
    
    result = collection.insert_one(apartment_data)
    if result is not None:
        # start_producer(result, operation_name="apartment_added")
        return get_inserted_result(result)
    else:
        return jsonify({'error': 'Could not add apartment'}), 500
    

def delete_apartment(apartment_id):
    collection = get_collection(apartments_collection)

    result = collection.delete_one({'_id': ObjectId(apartment_id)})
    if result.deleted_count > 0:
        start_producer(apartment_id, operation_name="apartment_removed")
        return jsonify({'message': f'Apartment {apartment_id} removed successfully'})
    else:
        return jsonify({'error': f'Apartment {apartment_id} not found'}), 500


if __name__ == "__main__":
   app.run(debug=True)
