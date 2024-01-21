from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

APARTMENT_MICROSERVICE_URL = 'http://apartment:5000'
BOOKING_MICROSERVICE_URL = 'http://booking:5000'
SEARCH_MICROSERVICE_URL = 'http://search:5000'


@app.route('/apartment/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def apartment_microservice(path):
    url = f'{APARTMENT_MICROSERVICE_URL}/{path}'
    return forward_request(url)


@app.route('/booking/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def booking_microservice(path):
    url = f'{BOOKING_MICROSERVICE_URL}/{path}'
    return forward_request(url)


@app.route('/search/<path:path>', methods=['GET'])
def search_microservice(path):
    url = f'{SEARCH_MICROSERVICE_URL}/{path}'
    return forward_request(url)


def forward_request(url):
    method = request.method
    params = request.args.to_dict()

    # Forward the request to the microservice
    try:
        response = requests.request(method=method, url=url, params=params)
        
        response_content_type = response.headers.get('Content-Type', '').lower()
        if 'application/json' in response_content_type:
            return jsonify(response.json()), response.status_code
        else:
            return response.text, response.status_code


    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000)