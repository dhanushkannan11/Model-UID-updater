import json
import pickle
import boto3
import os


def load_token():
    """
    Loads dropbox authentication token
    :return:
    """
    working_dir = os.getcwd()
    if "NeuraBubbles_and_Canisters" not in working_dir:
        working_dir = os.path.join(working_dir, "NeuraBubbles_and_Canisters")
    with open("data/token.pkl", "rb") as file:
        data = pickle.load(file)

    return data["aws_id"], data["aws_key"]


def compile_dynamodb_json(dictionary):
    """
    Transforms the Python dictionary to a format that can be interprated correctly by DynamoDB

    :param dictionary:
    :return:
    """
    dynamodb_dict = []

    for key in list(dictionary.keys()):
        dynamodb_dict.append(

            {
                "UID": key,
                "destinationShipped": "",
                "ID": dictionary[key],
                "raptured": False,
                "shippedStatus": True,
                "usageCount": 0,
                "usages": {
                    "timestamps": [
                    ],
                    "systemIDs": [
                    ],
                    "userEmailIDs": [
                    ],
                    "locations": [
                    ]
                }
            }
        )

    # save the compiled json file locally

    with open("data/dynamodb_models_iud_id.json", "w") as outfile:
        json.dump(dynamodb_dict, outfile, indent=4, separators=(',', ': '))

    return dynamodb_dict


class DynamoDB:

    def __init__(self, access_id, access_key, service_name, region, table_name):
        """

        :param access_id:
        :param access_key:
        :param service_name:
        :param region:
        :param table_name:
        """
        self.access_id = access_id
        self.access_key = access_key
        self.service_name = service_name
        self.region = region
        self.table_name = table_name
        self.client = None
        self.table = None

    def connect(self):
        """
        Connects to Dynamo DB in the region specified when initializing the DynamDB instance 

        :return:
        """
        self.client = boto3.resource(
            service_name=self.service_name,
            region_name=self.region,
            aws_access_key_id=self.access_id,
            aws_secret_access_key=self.access_key
        )

    def get_table(self):
        """
        Fetches data from the DynamoDB table name declared when initializing the instance.

        :return:
        """
        self.table = self.client.Table(self.table_name)
        return self.table.scan()

    def get_item(self, uid):
        """
        Takes the UID of a NeuraBubble and returns all the details about it stored in the database

        :param uid:
        :return:
        """

        return self.table.get_item(Key={"UID": uid})

    def update_item(self, json_object):
        """
        Pushes one item to the Database

        :param json_object:
        :return:
        """

        self.table.put_item(Item=json_object)

    def update_items(self, json_objects):
        """
        Takes a list containing all items to be updated in the database and pushes 
        each one of them to the DB 

        :param json_objects:
        :return:
        """
        for json_object in json_objects:
            self.update_item(json_object)

    def put_item(self, Item):
        
        response = self.table.put_item(Item=Item)
        return response

