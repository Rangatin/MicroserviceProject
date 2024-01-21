from bson import ObjectId

import requests


"""
/apartment/add?name=A&address=Bolzano&noiselevel=4&floor=0
/apartment/add?name=B&address=Merano&noiselevel=0&floor=2
/apartment/add?name=C&address=Trento&noiselevel=1&floor=1

----------------------------------------------------------------
/booking/add?apartment=(id of apartment A)&from=20240101&to=20240201&who=Matteo
/booking/add?apartment=(id of apartment B)&from=20240301&to=20240307&who=Paola
/booking/change?id=(id of previous booking)&from=20240301&to=20240308
/booking/cancel?id=(id of previous booking)
"""

get_apartment_url = 'http://localhost:5000/apartment/get'

add_apartment_url = 'http://localhost:5000/apartment/add'
remove_apartment_url = 'http://localhost:5000/apartment/remove'


trento_apartment_id = 0

def test_add_apartment_Bolzano():
    add_apartment_params =  create_apartment("A", "Bolzano", 4, 0)
 
    response = requests.post(add_apartment_url, params=add_apartment_params)
    inserted_id = response.json()["inserted_id"]

    assert response.status_code == 200
    assert inserted_id is not None

    response = requests.get(get_apartment_url, params={"id" : inserted_id})
    insert_result = response.json()

    assert_insert_apartment_equals(insert_result, "A", "Bolzano", 4, 0)


def test_add_apartment_Merano():
    add_apartment_params =  create_apartment("B", "Merano", 0, 2)
 
    response = requests.post(add_apartment_url, params=add_apartment_params)
    inserted_id = response.json()["inserted_id"]

    assert response.status_code == 200
    assert inserted_id is not None

    response = requests.get(get_apartment_url, params={"id" : inserted_id})
    insert_result = response.json()

    assert_insert_apartment_equals(insert_result, "B", "Merano", 0, 2)


def test_add_apartment_Trento():
    add_apartment_params =  create_apartment("C", "Trento", 1, 1)
 
    response = requests.post(add_apartment_url, params=add_apartment_params)
    inserted_id = response.json()["inserted_id"]

    assert response.status_code == 200
    assert inserted_id is not None

    response = requests.get(get_apartment_url, params={"id" : inserted_id})
    insert_result = response.json()

    assert_insert_apartment_equals(insert_result, "C", "Trento", 1, 1)


def test_remove_apartment_Trento():
    apartment_id = "65ad8e3687725a0c5247471a"
    response = requests.post(remove_apartment_url, params={"id" : apartment_id})
    delete_result = response.json()

    assert response.status_code == 200
    # self.assertEqual(delete_result.deleted_count, 1) --> update remove method in microservice

    # jsonify({'message': f'Apartment {apartment_id} removed successfully'})
    assert delete_result["message"] == f"Apartment {ObjectId(apartment_id)} removed successfully"


    


def create_apartment(name, address, noiselevel, floor):
    return {
        "name": name,
        "address": address,
        "noiselevel": noiselevel,
        "floor": floor
    }


def assert_insert_apartment_equals(insert_result, name, address, noiselevel, floor):
    assert insert_result["name"] == name
    assert insert_result["address"] == address
    assert insert_result["noiselevel"] is noiselevel
    assert insert_result["floor"] is floor



# # Test case for the Apartment microservice
# def test_apartment_microservice():
    

#     # Test removing an apartment
#     remove_apartment_url = 'http://localhost:5000/apartment/remove'
#     remove_apartment_params = {
#         'id': '123'
#     }
#     remove_apartment_response = requests.get(remove_apartment_url, params=remove_apartment_params)
#     assert remove_apartment_response.status_code == 200
    

#     # Test listing all apartments
#     list_apartments_url = 'http://localhost:5000/apartment/list'
#     list_apartments_response = requests.get(list_apartments_url)
#     assert list_apartments_response.status_code == 200
    


# # Test case for the Booking microservice
# def test_booking_microservice():
#     # Test adding a booking
#     add_booking_url = 'http://localhost:5000/booking/add'
#     add_booking_params = {
#         'apartment': '123',
#         'from': '20230101',
#         'to': '20230115',
#         'who': 'JohnDoe'
#     }
#     add_booking_response = requests.get(add_booking_url, params=add_booking_params)
#     assert add_booking_response.status_code == 200
#     # Add additional assertions as needed


# # Test case for the Search microservice
# def test_search_microservice():
#     # Test searching
#     search_url = 'http://localhost:5000/search'
#     search_params = {
#         'from': '20230101',
#         'to': '20230115'
#     }
#     search_response = requests.get(search_url, params=search_params)
#     assert search_response.status_code == 200
#     # Add additional assertions as needed


# # Test case for the API gateway
# def test_api_gateway():
#     # Test forwarding to the Apartment microservice
#     apartment_forward_url = 'http://localhost:5000/apartment/add'
#     apartment_forward_params = {
#         'name': 'ExampleName',
#         'address': 'ExampleAddress',
#         'noiselevel': '5',
#         'floor': '3'
#     }
#     apartment_forward_response = requests.get(apartment_forward_url, params=apartment_forward_params)
#     assert apartment_forward_response.status_code == 200
#     # Add additional assertions as needed

#     # Test forwarding to the Booking microservice
#     booking_forward_url = 'http://localhost:5000/booking/add'
#     booking_forward_params = {
#         'apartment': '123',
#         'from': '20230101',
#         'to': '20230115',
#         'who': 'JohnDoe'
#     }
#     booking_forward_response = requests.get(booking_forward_url, params=booking_forward_params)
#     assert booking_forward_response.status_code == 200
#     # Add additional assertions as needed

#     # Test forwarding to the Search microservice
#     search_forward_url = 'http://localhost:5000/search'
#     search_forward_params = {
#         'from': '20230101',
#         'to': '20230115'
#     }
#     search_forward_response = requests.get(search_forward_url, params=search_forward_params)
#     assert search_forward_response.status_code == 200
#     # Add additional assertions as needed