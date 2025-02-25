from pymongo import MongoClient


client = MongoClient('mongodb://localhost:27017/')
db = client['contact_db']
users_collection = db['users']
contacts_collection = db['contacts']


def get_user_by_username(username):
    return users_collection.find_one({'username': username})

def get_user_by_email(email):
    return users_collection.find_one({'email': email})

def add_user(username, password, email):
    user = {
        'username': username,
        'password': password,  
        'email': email,
    }
    users_collection.insert_one(user)


def add_contact(mobile, email, address, registration_number):
    contact = {
        'mobile': mobile,
        'email': email,
        'address': address,
        'registration_number': registration_number,
    }
    contacts_collection.insert_one(contact)

def get_contact_by_registration_number(registration_number):
    return contacts_collection.find_one({'registration_number': registration_number})