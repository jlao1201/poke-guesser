"""
    Script to retrieve pokemon names/sprites and add to MongoDB database.
"""

from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup as bs
import config


client = MongoClient(f"mongodb+srv://{config.DB_USER}:{config.DB_PASS}@cluster0.pvvk0.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client['poke-guesser']
collection = db['pokemon']

post_list = []
names = []
images = []
images_large = []


def load_names():
    """ Get all Pokemon names. """
    url = 'https://pokemondb.net/pokedex/national'
    response = requests.get(url)
    soup = bs(response.content, 'html.parser')
    for link in soup.findAll(class_='ent-name'):
        names.append(link.text)


def load_images():
    """ Get small sprite images for each Pokemon. """
    url = 'https://pokemondb.net/pokedex/national'
    response = requests.get(url)
    soup = bs(response.content, 'html.parser')
    for link in soup.find_all('span'):
        if link.get('data-src') is not None:
            images.append(link.get('data-src'))


def load_images_large():
    """ Get large sprite images for each Pokemon. """
    new_names = [doc['name'] for doc in collection.find()]
    lower_names = [x.lower() for x in new_names]
    for i in range(len(new_names)):
        url = f'https://pokemondb.net/pokedex/{lower_names[i]}'
        response = requests.get(url)
        soup = bs(response.content, 'html.parser')
        link = soup.find('img')
        images_large.append(link.get('src'))
        collection.update_one({'name': new_names[i]}, {'$set': {'img-src-large': images_large[i]}})


def add_posts():
    """ Create and add posts to MongoDB database. """
    for i in range(len(names)):
        post = {'name': names[i], 'img-src': images[i]}
        post_list.append(post)
    collection.insert_many(post_list)


def print_data():
    """ Display all documents in database. """
    for doc in collection.find():
        print(doc)


if __name__ == '__main__':
    print_data()
