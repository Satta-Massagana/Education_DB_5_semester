import uuid
import random
from pymongo import MongoClient, ASCENDING

def generate_test_data():
    with MongoClient("mongodb://localhost:27017/") as client:
        db = client["customer"]
        collection = db["reviews"]
        collection.drop()
        for i in range(1000):
            id = str(uuid.uuid4())
            review_dict = {
                "_id": id,
                "user_id": str(random.randint(1, 10)),
                "order_data": {
                    "order_id": str(uuid.uuid4()),
                    "product_id": str(random.randint(1, 10))
                },
                "rating": random.randint(1, 10),
                "content": "some text"
            }
            collection.update_one(filter={"_id": id}, update={"$set": review_dict}, upsert=True)
        collection.create_index([("user_id", ASCENDING)])
        collection.create_index([("order_data.product_id", ASCENDING)])
        collection.create_index([("rating", ASCENDING)])
        print('Generated test data and created indexes')

class MongoReviews:
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", 
                 db_name: str = "customer", collection_name: str = "reviews"):
        self.client = MongoClient(connection_string)
        self.collection = self.client[db_name][collection_name]

    def get_user_report(self):
        pipeline_by_user = [
            {"$group": {
                "_id": "$user_id",
                "total_reviews": {"$sum": 1},
                "average_rating": {"$avg": "$rating"}
            }},
            {"$sort": {"total_reviews": -1}}
        ]
        return list(self.collection.aggregate(pipeline_by_user))

    def get_product_report_by_product(self, product_id: str):
        pipeline_specific_product = [
            {"$match": {"order_data.product_id": product_id}},
            {"$group": {
                "_id": "$order_data.product_id",
                "total_reviews": {"$sum": 1},
                "average_rating": {"$avg": "$rating"},
                "min_rating": {"$min": "$rating"},
                "max_rating": {"$max": "$rating"}
            }}
        ]
        return list(self.collection.aggregate(pipeline_specific_product))

# generate_test_data()
mongo_reviews = MongoReviews()
# print(mongo_reviews.get_user_report())
print(mongo_reviews.get_product_report_by_product("2"))
