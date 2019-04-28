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
        #todo move to func
        if sort_by != 0:
            if sort_order == 'asc':
                sort_order = 1
            elif sort_order == 'desc':
                sort_order = -1
        if limit is not None:
            #todo move to func
            if sort_order != 0:
                results = machines.find({}, self.query_projections).sort(sort_by, sort_order).skip(int(last_batch_fetched)).limit(int(limit))
            else:
                results = machines.find({}, self.query_projections).skip(int(last_batch_fetched)).limit(int(limit))
        else:  
            # todo move to func
            if sort_order != 0:
                results = machines.find({}, self.query_projections).sort(
                    sort_by, sort_order)
            else:
                results = machines.find({}, self.query_projections)
        return {'count': results.count(), 'data': helpr.clean_for_read(list(results))}

    def get_machines_by_property(self, property, limit, last_batch_fetched, sort_by, sort_order):
        machines = self.db.machines
        #todo move to func
        if sort_by != 0:
            if sort_order == 'asc':
                sort_order = 1
            elif sort_order == 'desc':
                sort_order = -1
        if limit is not None:
            #todo move to func
            if property.startswith('"') and property.endswith('"'):
                if sort_order != 0:
                    results = machines.find({'$text': {'$search': property}}, self.query_projections).sort(
                        [('score', {'$meta': 'textScore'}), (sort_by, sort_order)]).skip(int(last_batch_fetched)).limit(int(limit))
                else:
                    results = machines.find({'$text': {'$search': property}}, self.query_projections).sort(
                        [('score', {'$meta': 'textScore'})]).skip(int(last_batch_fetched)).limit(int(limit))
            else:
                if sort_order != 0:
                    results = machines.find({'$or': helpr.like(property)}, self.query_projections).sort(
                        sort_by, sort_order).skip(int(last_batch_fetched)).limit(int(limit))
                else:
                    results = machines.find({'$or': helpr.like(property)}, self.query_projections).skip(
                        int(last_batch_fetched)).limit(int(limit))
        else:
            #todo move to func
            if property.startswith('"') and property.endswith('"'):
                if sort_order != 0:
                    results = machines.find({'$text': {'$search': property}}, self.query_projections).sort(
                        [('score', {'$meta': 'textScore'}), (sort_by, sort_order)])
                else:
                    results = machines.find({'$text': {'$search': property}}, self.query_projections).sort(
                        [('score', {'$meta': 'textScore'})])
            else:
                if sort_order != 0:
                    results = machines.find({'$or': helpr.like(property)}, self.query_projections).sort(
                        sort_by, sort_order)
                else:
                    results = machines.find({'$or': helpr.like(property)}, self.query_projections)
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
    key = 'tncDate'
    # for machine in mgr.get_machines():
    #     if not machine[key]:
    #         mgr.update_machine(machine['serialNumber'], {
    #                            key: None})
    #         continue
        # date_tokens = re.split('[/: ]', machine[key])
        # print(date_tokens)
        # # new_date = date_tokens[1] + '/' + \
        # #     date_tokens[0] + '/' + date_tokens[2]
        # new_date = datetime.datetime(int(date_tokens[2]), int(
        #     date_tokens[1]), int(date_tokens[0]), int(date_tokens[3]), int(date_tokens[4]), int(date_tokens[5]))
        # print(machine[key] + ' --> ' + str(new_date))
        # mgr.update_machine(machine['serialNumber'], {
        #                    key: new_date})


