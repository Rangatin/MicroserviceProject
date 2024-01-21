from flask import Flask, jsonify, request
from bson import ObjectId, json_util
from pymongo import MongoClient
from dotenv import load_dotenv

import os
import json
import pika
import threading
import time

load_dotenv()

db_url = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

connection_params = pika.ConnectionParameters('rabbitmq', port=5672)
queue_name = 'main_message_queue'

client = MongoClient(db_url)
database_name = "booking_db"

bookings_collection = "bookings"
apartments_collection = "apartments"


def get_collection(collection_name):
    return client[database_name][collection_name]


@app.route('/')
def hello():
    return "Hello from booking microservice"


@app.route('/get', methods=['GET'])
def get_single_booking():
    booking_id = request.args.get('id')

    if not booking_id:
        return jsonify({"error": "Missing booking id"}), 400
    
    result = get_collection(bookings_collection).find_one({"_id" : ObjectId(booking_id)})
    return json_util.dumps(result)


@app.route('/add', methods=['POST'])
def add_booking():
    apartment_id = request.args.get('apartment')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    who = request.args.get('who')

    if not all([apartment_id, from_date, to_date, who]):
        return jsonify({"error": "Missing required parameters"}), 400

    booking_data = create_booking(apartment_id, from_date, to_date, who)
    return insert_booking(booking_data)


@app.route('/cancel', methods=['POST'])
def cancel_booking():
    booking_id = request.args.get('id')

    if not booking_id:
        return jsonify({"error": "Missing booking id"}), 400

    return delete_booking(booking_id)


@app.route('/change', methods=['POST'])
def change_booking():
    booking_id = request.args.get('id')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if not all([booking_id, from_date, to_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    booking_data = create_change_booking(booking_id, from_date, to_date)
    return update_booking(booking_data)


@app.route('/list', methods=['GET'])
def list_bookings():
    bookings = get_collection("booking_apartments").find()
    bookings_json = json.dumps(list(bookings), default=str)
    return jsonify(bookings_json)



def create_booking(apartment_id, from_date, to_date, who):
    return {
        "_id": ObjectId(),
        "aparment": apartment_id,
        "from_date": from_date,
        "to_date": to_date,
        "who": who
    }


def get_inserted_result(insert_result):
    response_data = {
        # "acknowledged": insert_result.acknowledged,
        "inserted_id": str(insert_result.inserted_id)  # Convert ObjectId to string for JSON serialization
    }

    return jsonify(response_data)


def create_change_booking(booking_id, from_date, to_date):
    return {
        "id": booking_id,
        "from_date": from_date,
        "to_date": to_date
    }


def insert_booking(booking_data):
    collection = get_collection(bookings_collection)
    
    result = collection.insert_one(booking_data)
    if result is not None:
        # start_producer(booking_data, operation_name="booking_added")
        return get_inserted_result(result)
    else:
        return jsonify({'error': 'Could not add booking'}), 500


def update_booking(booking_data):
    collection = get_collection(bookings_collection)
    
    booking_id = booking_data["id"]

    result = collection.update_one(
        {'_id': ObjectId(booking_id)},
        {'$set': {'from': booking_data["from"], 'to': booking_data["to"]}}
    )

    if result.modified_count > 0:
        # start_producer(booking_data, operation_name="booking_changed")
        return jsonify({'message': 'Booking changed successfully'})
    else:
        return jsonify({'error': f'Could not change booking {booking_id}'}), 500


def delete_booking(booking_id):
    collection = get_collection(bookings_collection)

    result = collection.delete_one({'_id': ObjectId(booking_id)})
    if result.deleted_count > 0:
        # start_producer(booking__id, operation_name="booking_removed")
        return jsonify({'message': f'Booking {booking_id} removed successfully'})
    else:
        return jsonify({'error': f'Booking {booking_id} not found'}), 500




def establish_connection():
    while True:
        try:
            connection = pika.BlockingConnection(connection_params)
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error connecting to RabbitMQ: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)


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


def start_apartments_consumer():
    connection = establish_connection()
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=process_message, auto_ack=True)
    channel.start_consuming()


def insert_apartment(apartment_data):
    collection = get_collection(apartments_collection)
    
    result = collection.insert_one(apartment_data)
    if result is not None:
        return get_inserted_result(result)
    else:
        return jsonify({'error': 'Could not add apartment'}), 500
    

def delete_apartment(apartment_id):
    collection = get_collection(apartments_collection)

    result = collection.delete_one({'_id': apartment_id})
    if result.deleted_count > 0:
        return jsonify({'message': f'Apartment {apartment_id} removed successfully'})
    else:
        return jsonify({'error': f'Apartment {apartment_id} not found'}), 500


def process_message(ch, method, properties, body):
    try:
        message = json.loads(body)

        if all(["operation", "apartment"]) not in message:
            return

        operation_type = message["operation"]
        apartment_object = message["apartment"]

        if operation_type == "apartment_added":
           insert_apartment(apartment_object)

        elif operation_type == "apartment_removed":
           delete_apartment(apartment_object)
            
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")


if __name__ == "__main__":
    consumer_thread = threading.Thread(target=start_apartments_consumer)
    consumer_thread.start()
    app.run(debug=True)