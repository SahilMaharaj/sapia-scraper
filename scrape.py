from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup MongoDB connection using environment variables for security
mongo_connection_string = os.getenv('MONGO_CONNECTION_STRING', 'default_connection_string_if_not_set')
client = MongoClient(mongo_connection_string)
db = client.webData
collection = db.scrapes

@app.route('/scrape')
def scrape():
    url = "https://www.sapia.org.za/fuel-prices/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            h2_elements = soup.find_all('h2')
            if not h2_elements:
                logging.warning('No <h2> tags found on the page.')
            h2_texts = [h2.text.strip() for h2 in h2_elements]
        else:
            logging.error(f'Failed to retrieve content, status code {response.status_code}')
            return jsonify({'error': 'Failed to retrieve content'}), 500
    except requests.RequestException as e:
        logging.error(f'Error accessing the page: {e}')
        return jsonify({'error': 'Error accessing the page'}), 500

    data = {
        'date': datetime.now(),
        'h2': h2_texts
    }
    result = collection.insert_one(data)

    # Remove the '_id' key from the data dictionary before returning it
    data.pop('_id', None)

    return jsonify(data), 200

@app.route('/data')
def get_data():
    try:
        data = list(collection.find({}, {'_id': 0}).sort('date', -1))
        return jsonify(data), 200
    except Exception as e:
        logging.error(f'Error retrieving data from MongoDB: {e}')
        return jsonify({'error': 'Database error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to 5000 if no PORT environment variable is set
    app.run(host='0.0.0.0', port=port)
