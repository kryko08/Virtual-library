import os
from dotenv import load_dotenv

from pymongo import MongoClient

import pandas as pd
import random


def add_books(csv_path, book_collection):

    dataframe = pd.read_csv(csv_path)

    for index, row in dataframe.iterrows():
        author = row["author"]
        book_title = row["title"]
        number_of_pages = row["pages"]
        year_published = random.randint(1500, 2022)
        number_of_licences = random.randint(1, 5)

        book_collection.insert_one(
            {
                "author": author,
                "book_title": book_title,
                "number_of_pages": number_of_pages,
                "year_published": year_published,
                "number_of_licences": number_of_licences,
                "licences_available": number_of_licences
            }
        )

        if index == 100:
            break

def add_licences_available_field(book_collection):
    pipeline = [
    {
        '$match': {}
    }, {
        '$set': {
            'licences_availabel': '$number_of_licences'
        }
    }]
    book_collection.aggregate(pipeline)




if __name__ == '__main__':
    load_dotenv()
    path_to_csv = os.getenv('PATH_TO_CSV')
    MONGO_URI = os.getenv('MONGO_URI') 

    # get book collection
    client = MongoClient(MONGO_URI)
    db = client["library"]
    books = db["books"]

    add_books(path_to_csv, books)
