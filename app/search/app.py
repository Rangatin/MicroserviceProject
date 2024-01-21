from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

import json
import pika
import threading


app = Flask(__name__)

connection_params = pika.ConnectionParameters('rabbitmq', port=5672)
queue_name = 'main_message_queue'

CONNECTION_STRING = "mongodb+srv://inkoment:fTkEai7e59QGvKId@contemporarycluster.apusbpu.mongodb.net/ContemporaryCluster"
client = MongoClient(CONNECTION_STRING)
database_name = "search_db"


bookings_collection = "bookings"
apartments_collection = "apartments"


def get_collection(collection_name):
    return client[database_name][collection_name]


@app.route('/')
def hello():
   return "Hello from search microservice"


@app.route("/search")
def search_appartments():
   search_from = request.args.get('from')
   search_to = request.args.get('to')

   if search_from is None:
      return jsonify({"error": "Missing from parameter"}), 400

   available_apartments = []

   """
   1. Get apartments
   2. For each aparment, if booking not exist for provided dates 
   add to collection

   3. Return final collection

   """

   apartments = get_collection(apartments_collection).find()
   bookings = get_collection(bookings_collection).find()

   for aparment in apartments:
      booking = bookings.find_one({"apartment_id": aparment["id"]})

      if booking is None:
         available_apartments.append(aparment)
      elif do_date_ranges_not_intersect(booking["from"], booking["to"], search_from, search_to):
         available_apartments.append(aparment)

   return jsonify({"available apartments": apartments})



def do_date_ranges_not_intersect(from_date1, to_date1, from_date2, to_date2):
    # Convert string dates to datetime objects
    from_date1 = datetime.strptime(from_date1, '%Y-%m-%d')
    to_date1 = datetime.strptime(to_date1, '%Y-%m-%d')
    from_date2 = datetime.strptime(from_date2, '%Y-%m-%d')
    to_date2 = datetime.strptime(to_date2, '%Y-%m-%d')

    # Check if the date ranges do not intersect
    return to_date1 < from_date2 or to_date2 < from_date1


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
        return get_inserted_result(result)
    else:
        return jsonify({'error': 'Could not add apartment'}), 500
    

def delete_apartment(apartment_id):
    collection = get_collection(apartments_collection)

    result = collection.delete_one({'_id': ObjectId(apartment_id)})
    if result.deleted_count > 0:
        return jsonify({'message': f'Apartment {apartment_id} removed successfully'})
    else:
        return jsonify({'error': f'Apartment {apartment_id} not found'}), 500
    

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




def manage_aparment(operation_type, apartment_object): 
   if operation_type == "apartment_added":
      insert_apartment(apartment_object)

   elif operation_type == "apartment_removed":
      delete_apartment(apartment_object)


def manage_booking(operation_type, booking_object): 
   if operation_type == "booking_added":
      insert_booking(booking_object)

   elif operation_type == "booking_removed":
      delete_booking(booking_object)



def process_message(ch, method, properties, body):
   try:
      message = json.loads(body)

      if "operation" and ("apartment" or "booking") not in message:
         return
      
      operation_type = message["operation"]
      
      if "apartment" in message:
         manage_aparment(operation_type, message["apartment"])

      elif "booking" in message:
         manage_booking(operation_type, message["booking"])

   except json.JSONDecodeError as e:
      print(f"Error decoding JSON: {e}")


def start_consumer():
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=process_message, auto_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.start()
    app.run(debug=True)
