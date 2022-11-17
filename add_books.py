import os
from dotenv import load_dotenv

from pymongo import MongoClient

import pandas as pd
import random

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI') 

# get book collection
client = MongoClient(MONGO_URI)
db = client["library"]
books = db["books"]

# load csv file 
path_to_csv = os.getenv('PATH_TO_CSV')

dataframe = pd.read_csv(path_to_csv)

for index, row in dataframe.iterrows():
    author = row["author"]
    book_title = row["title"]
    number_of_pages = row["pages"]
    year_published = random.randint(1500, 2022)
    number_of_licences = random.randint(1, 5)

    books.insert_one(
        {
            "author": author,
            "book_title": book_title,
            "number_of_pages": number_of_pages,
            "year_published": year_published,
            "number_of_licences": number_of_licences
        }
    )

    if index == 100:
        break



