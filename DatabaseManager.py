from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime, re

class DatabaseManager:
    def __init__(self, host, port, db_name):
        client = MongoClient(host, port)
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

    def _clean(self, machines):
        for machine in machines:
            if machine['tncDate'] is not None:
                machine['tncDate'] = machine['tncDate'].strftime('%d/%m/%Y')
            if machine['ppmDate'] is not None:
                machine['ppmDate'] = machine['ppmDate'].strftime('%d/%m/%Y')
            if machine['dateOfCreation'] is not None:
                machine['dateOfCreation'] = machine['dateOfCreation'].strftime(
                    '%d/%m/%Y %H:%M:%S')
            if machine['lastUpdated'] is not None:
                machine['lastUpdated'] = machine['lastUpdated'].strftime(
                    '%d/%m/%Y %H:%M:%S')
        return machines

    def _convert_string_to_date(self, date_as_str, add_days=0):
        try:
            date_as_date = datetime.datetime.strptime(date_as_str, '%d-%m-%Y')
        except ValueError:
            return date_as_str
        return date_as_date + datetime.timedelta(days=add_days)

    def _convert_string_to_datetime(self, date_as_str, add_days=0):
        try:
            date_as_datetime = datetime.datetime.strptime(date_as_str, '%d-%m-%Y %H:%M:%S')
        except ValueError:
            return date_as_str
        return date_as_datetime + datetime.timedelta(days=add_days)

    def _like(self, property):
        return [{'serialNumber': {'$regex': property, '$options': 'i'}},
                {'customer': {'$regex': property, '$options': 'i'}},
                {'state': {'$regex': property, '$options': 'i'}},
                {'district': {'$regex': property, '$options': 'i'}},
                {'accountType': {'$regex': property, '$options': 'i'}},
                {'model': {'$regex': property, '$options': 'i'}},
                {'brand': {'$regex': property, '$options': 'i'}},
                {'status': {'$regex': property, '$options': 'i'}},
                {'tncDate': self._convert_string_to_date(property)},
                {'ppmDate': self._convert_string_to_date(property)},
                {'reportedBy': {'$regex': property, '$options': 'i'}},
                {'personInCharge': {'$regex': property, '$options': 'i'}},
                {'dateOfCreation': self._convert_string_to_datetime(property)},
                {'lastUpdated': self._convert_string_to_datetime(property)},
                {'dateOfCreation': {'$gte': self._convert_string_to_date(property), '$lt': self._convert_string_to_date(property, 1)}},
                {'lastUpdated': {'$gte': self._convert_string_to_date(property), '$lt': self._convert_string_to_date(property, 1)}}
               ]

    def get_machines(self, limit, last_batch_fetched, sort_by, sort_order):
        machines = self.db.machines
        if sort_by != 0:
            if sort_order == 'asc':
                sort_order = 1
            elif sort_order == 'desc':
                sort_order = -1
        if limit is not None:
            if sort_order != 0:
                results = machines.find({}, self.query_projections).sort(sort_by, sort_order).skip(int(last_batch_fetched)).limit(int(limit))
            else:
                results = machines.find({}, self.query_projections).skip(int(last_batch_fetched)).limit(int(limit))
        else:
            #todo
            pass
        return {'count': results.count(), 'data': self._clean(list(results))}

    def get_machines_by_property(self, property, limit, last_batch_fetched, sort_by, sort_order):
        machines = self.db.machines
        if sort_by != 0:
            if sort_order == 'asc':
                sort_order = 1
            elif sort_order == 'desc':
                sort_order = -1
        if limit is not None:
            if property.startswith('"') and property.endswith('"'):
                if sort_order != 0:
                    results = machines.find({'$text': {'$search': property}}, self.query_projections).sort(
                        [('score', {'$meta': 'textScore'}), (sort_by, sort_order)]).skip(int(last_batch_fetched)).limit(int(limit))
                else:
                    results = machines.find({'$text': {'$search': property}}, self.query_projections).sort(
                        [('score', {'$meta': 'textScore'})]).skip(int(last_batch_fetched)).limit(int(limit))
            else:
                if sort_order != 0:
                    results = machines.find({'$or': self._like(property)}, self.query_projections).sort(
                        sort_by, sort_order).skip(int(last_batch_fetched)).limit(int(limit))
                else:
                    results = machines.find({'$or': self._like(property)}, self.query_projections).skip(int(last_batch_fetched)).limit(int(limit))
        else:
            #todo
            pass
        return {'count': results.count(), 'data': self._clean(list(results))}

    def get_machine_by_id(self, id):
        machines = self.db.machines
        return machines.find_one({'serialNumber': id}, self.query_projections)

    def update_machine(self, id, new_values):
        machines = self.db.machines
        machines.update_one({'serialNumber': id}, {'$set': new_values})


if __name__ == "__main__":
    mgr = DatabaseManager('localhost', 27017, 'emblem')
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


