from pymongo import MongoClient, errors
from bson.objectid import ObjectId
import datetime, re
import helpr

class DatabaseManager:
    def __init__(self, uri, db_name):
        client = MongoClient(uri)
        self.db = client[db_name]
        self.query_projections = {
            # Exclude
            '_id': 0,
            'overdue': 0, 
            'tncDateInDate': 0, 
            'ppmDateInDate': 0, 
            'almostDue': 0, 
            'additionalNotes': 0, 
            'lastUpdatedInLong': 0, 
            'historyCount': 0, 
            'dueForPPM': 0, 
            'dueStatus': 0, 
            'ppmDateInString': 0, 
            'tncDateInString': 0, 
            'dateOfCreationInLong': 0,
            # Include
            'score': {'$meta': 'textScore'}
        }

    def get_machines(self, limit, last_batch_fetched, sort_by, sort_order):
        machines = self.db.machines
        results = machines.find({}, self.query_projections)
        if sort_by is not None:
            results = results.sort(sort_by, helpr.get_sort_order(sort_order))
        if limit is not None:
            results = results.skip(int(last_batch_fetched)).limit(int(limit))
        return {'count': results.count(), 'data': helpr.clean_for_read(list(results))}

    def get_machines_by_property(self, property, limit, last_batch_fetched, sort_by, sort_order):
        machines = self.db.machines
        if property.startswith('"') and property.endswith('"'):
            search_type = '$text'
            search_val = {'$search': property}
        else:
            search_type = '$or'
            search_val = helpr.like(property)
        results = machines.find({search_type: search_val}, self.query_projections)
        if sort_by is not None:
            results = results.sort([('score', {'$meta': 'textScore'}), (sort_by, helpr.get_sort_order(sort_order))])
        if limit is not None:
            results = results.skip(int(last_batch_fetched)).limit(int(limit))
        return {'count': results.count(), 'data': helpr.clean_for_read(list(results))}

    def get_machine_by_id(self, id):
        machines = self.db.machines
        return machines.find_one({'serialNumber': id}, self.query_projections)

    def update_machine(self, id, new_values):
        machines = self.db.machines
        try:
            machines.update_one({'serialNumber': id}, {'$set': helpr.clean_for_write(new_values)})
        except errors.PyMongoError:
            return False
        return True


if __name__ == "__main__":
    mgr = DatabaseManager('mongodb://localhost:27017/', 'emblem')


