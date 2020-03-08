from pymongo import MongoClient, errors
from bson.objectid import ObjectId
import datetime, re
import helpr
import gridfs
import pprint

class DatabaseManager:
    def __init__(self, uri, db_name):
        client = MongoClient(uri)
        self.db = client[db_name]
        self.gfs = gridfs.GridFS(self.db)
        self.query_project_id_only = {'serialNumber' : 1}
        self.query_projections = {
            # Exclude
            # '_id': 0,
            'overdue': 0, 
            'tncDateInDate': 0, 
            'ppmDateInDate': 0, 
            'almostDue': 0,
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

    def get_machines(self, limit, last_batch_fetched, sort_by, sort_order, due_status=None):
        machines = self.db.machines
        if not due_status:
            results = machines.find({}, self.query_projections)
        else:
            results = self._get_custom_due_machines(due_status)
        if sort_by is not None:
            results = results.sort(sort_by, helpr.get_sort_order(sort_order))
        if limit is not None:
            results = results.skip(int(last_batch_fetched)).limit(int(limit))
        results_as_list = list(results)
        self._map_history_to_machines(results_as_list)
        return {'count': results.count(), 'data': helpr.clean_for_read(results_as_list)}

    def _map_history_to_machines(self, machines):
        for machine in machines:
            history = self.get_history(machine['serialNumber'], None, None, None, None)
            machine['historyCount'] = history['count']
        return machines

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
        results_as_list = list(results)
        self._map_history_to_machines(results_as_list)
        return {'count': results.count(), 'data': helpr.clean_for_read(results_as_list)}

    def get_machine_by_id(self, id):
        machines = self.db.machines
        return helpr.clean_single_object_for_read(machines.find_one({'serialNumber': id}, self.query_projections) or {})

    def get_machines_by_ids(self, ids):
        machines = self.db.machines
        results = machines.find({'serialNumber': {'$in': ids}}, self.query_projections)
        return {'count': results.count(), 'data': helpr.clean_for_read(list(results))}

    # def _get_due_machines(self):
    #     machines = self.db.machines
    #     today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    #     due_today = machines.find({'ppmDate': today}, self.query_projections)
    #     return due_today

    # def _get_overdue_machines(self):
    #     machines = self.db.machines
    #     today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    #     two_weeks_ago = today + datetime.timedelta(days=-14)
    #     overdue = machines.find({'ppmDate': two_weeks_ago}, self.query_projections)
    #     return overdue

    # def _get_almost_due_machines(self):
    #     machines = self.db.machines
    #     today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    #     two_weeks_from_today = today + datetime.timedelta(days=14)
    #     almost_due = machines.find({'ppmDate': two_weeks_from_today}, self.query_projections)
    #     return almost_due

    def _get_custom_due_machines(self, status):
        machines = self.db.machines
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        two_weeks_from_today = today + datetime.timedelta(days=14)
        two_weeks_ago = today + datetime.timedelta(days=-14)
        tokens = status.split(",")
        conditions = []
        for token in tokens:
            if token == 'almostDue':
                conditions.append({'ppmDate': {'$lt': two_weeks_from_today, '$gte': today}})
            elif token == 'due':
                conditions.append({'ppmDate': today})
            elif token == 'overDue':
                conditions.append({'ppmDate': {'$lt': today, '$gte': two_weeks_ago}})
        due = machines.find({'$or': conditions}, self.query_projections)
        return due

    def _get_all_due_machines(self):
        machines = self.db.machines
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        two_weeks_from_today = today + datetime.timedelta(days=14)
        two_weeks_ago = today + datetime.timedelta(days=-14)
        due = machines.find({'$or': [{'ppmDate': today},
                                     {'ppmDate': {'$lt': two_weeks_from_today, '$gte': today}},
                                     {'ppmDate': {'$lt': today, '$gte': two_weeks_ago}}]}, self.query_projections)
        return due

    def get_num_of_due_machines(self):
        due = self._get_all_due_machines()
        return due.count()

    def insert_machine(self, new_machine):
        machines = self.db.machines
        machine = self.get_machine_by_id(new_machine['serialNumber'])
        if machine:
            return False
        return machines.insert_one(helpr.clean_for_write(new_machine))

    def update_machine(self, id, new_values):
        machines = self.db.machines
        machine = self.get_machine_by_id(id)
        if not machine:
            return False
        if machine['lastUpdated'] != new_values['lastUpdated']:
            return False
        if 'attachment' in machine and machine['attachment']:
            current_attachment_id = machine['attachment']
            if 'attachment' not in new_values or not new_values['attachment']:
                self.delete_attachment(current_attachment_id)
            elif new_values['attachment'] != current_attachment_id:
                self.delete_attachment(current_attachment_id)
        return machines.update_one({'serialNumber': id}, {'$set': helpr.clean_for_write(new_values)})

    def delete_machine(self, id):
        machines = self.db.machines
        machine = self.get_machine_by_id(id)
        if not machine:
            return False
        if 'attachment' in machine and machine['attachment']:
            self.delete_attachment(machine['attachment'])
        return machines.delete_one({'serialNumber': id})

    def insert_attachment(self, id, attachment, filename):
        attachment_id = self.gfs.put(attachment, parent_id=id, filename=filename)
        return {'id': str(attachment_id)}

    def get_attachment(self, id):
        gfs = self.gfs
        return gfs.get(ObjectId(id))

    def delete_attachment(self, id):
        gfs = self.gfs
        return gfs.delete(ObjectId(id))

    def get_history(self, machine_id, limit, last_batch_fetched, sort_by, sort_order):
        history = self.db.maintenance
        results = history.find({'serialNumber': machine_id}, self.query_projections)
        if sort_by is not None:
            results = results.sort(sort_by, helpr.get_sort_order(sort_order))
        if limit is not None:
            results = results.skip(int(last_batch_fetched)).limit(int(limit))
        return {'count': results.count(), 'data': helpr.clean_for_read(list(results))}

    def get_history_by_property(self, machine_id, property, limit, last_batch_fetched, sort_by, sort_order):
        history = self.db.maintenance
        if property.startswith('"') and property.endswith('"'):
            search_type = '$text'
            search_val = {'$search': property}
        else:
            search_type = '$or'
            search_val = helpr.like(property)
        results = history.find({'serialNumber': machine_id, search_type: search_val}, self.query_projections)
        if sort_by is not None:
            results = results.sort([('score', {'$meta': 'textScore'}), (sort_by, helpr.get_sort_order(sort_order))])
        if limit is not None:
            results = results.skip(int(last_batch_fetched)).limit(int(limit))
        return {'count': results.count(), 'data': helpr.clean_for_read(list(results))}

    def get_history_by_id(self, id):
        history = self.db.maintenance
        return helpr.clean_single_object_for_read(history.find_one({'_id': ObjectId(id)}, self.query_projections) or {})

    def insert_history(self, new_history):
        history = self.db.maintenance
        return history.insert_one(helpr.clean_for_write(new_history))

    def update_history(self, id, new_values):
        history = self.db.maintenance
        record = self.get_history_by_id(id)
        if not record:
            return False
        if record['lastUpdated'] != new_values['lastUpdated']:
            return False
        if 'attachment' in record and record['attachment']:
            current_attachment_id = record['attachment']
            if 'attachment' not in new_values or not new_values['attachment']:
                self.delete_attachment(current_attachment_id)
            elif new_values['attachment'] != current_attachment_id:
                self.delete_attachment(current_attachment_id)
        return history.update_one({'_id': ObjectId(id)}, {'$set': helpr.clean_for_write(new_values)})

    def delete_history(self, id):
        history = self.db.maintenance
        record = self.get_history_by_id(id)
        if not record:
            return False
        if 'attachment' in record and record['attachment']:
            self.delete_attachment(record['attachment'])
        return history.delete_one({'_id': ObjectId(id)})

if __name__ == "__main__":
    from pymongo import TEXT

    mgr = DatabaseManager('mongodb://localhost:27017/', 'emblem_2')
    # machines = mgr.db.machines
    # machines.create_index([('$**', TEXT)])
    # results = machines.find({}, mgr.query_projections)
    # for r in results:
    #     r['attachment'] = ''
    #     r['attachment_name'] = ''
    #     if r['tncDate'] is not None and r['tncDate'] != '':
    #         tokens = re.split('[/: ]', r['tncDate'])
    #         tmp = datetime.datetime(int(tokens[2]), int(tokens[0]), int(tokens[1]))
    #         r['tncDate'] = tmp
    #         r['tncDateInInt'] = str(int(tokens[2] + tokens[0] + tokens[1]))

    #     if r['ppmDate'] is not None and r['ppmDate'] != '':
    #         tokens = re.split('[/: ]', r['ppmDate'])
    #         tmp = datetime.datetime(int(tokens[2]), int(tokens[0]), int(tokens[1]))
    #         r['ppmDate'] = tmp
    #         r['ppmDateInInt'] = str(int(tokens[2] + tokens[0] + tokens[1]))

    #     if r['dateOfCreation'] is not None and r['dateOfCreation'] != '':
    #         tokens = re.split('[/: ]', r['dateOfCreation'])
    #         tmp = datetime.datetime(int(tokens[2]), int(tokens[0]), int(tokens[1]), int(tokens[3]), int(tokens[4]), int(tokens[5]))
    #         r['dateOfCreation'] = tmp
    #         r['dateOfCreationInInt'] = str(int(tokens[2] + tokens[0] + tokens[1] + tokens[3] + tokens[4] + tokens[5]))

    #     if r['lastUpdated'] is not None and r['lastUpdated'] != '':
    #         tokens = re.split('[/: ]', r['lastUpdated'])
    #         tmp = datetime.datetime(int(tokens[2]), int(tokens[0]), int(tokens[1]), int(tokens[3]), int(tokens[4]), int(tokens[5]))
    #         r['lastUpdated'] = tmp
    #         r['lastUpdatedInInt'] = str(int(tokens[2] + tokens[0] + tokens[1] + tokens[3] + tokens[4] + tokens[5]))
        
    #     print(r)
    #     machines.update_one({'_id': r['_id']}, {'$set': r})

    history = mgr.db.maintenance
    history.create_index([('$**', TEXT)])
    results = history.find({}, mgr.query_projections)
    for r in results:
        r['attachment'] = ''
        r['attachment_name'] = ''
        if r['workOrderDate'] is not None and r['workOrderDate'] != '':
            tokens = re.split('[/: ]', r['workOrderDate'])
            tmp = datetime.datetime(int(tokens[2]), int(tokens[0]), int(tokens[1]))
            r['workOrderDate'] = tmp
            r['workOrderDateInInt'] = str(int(tokens[2] + tokens[0] + tokens[1]))

        if r['dateOfCreation'] is not None and r['dateOfCreation'] != '':
            tokens = re.split('[/: ]', r['dateOfCreation'])
            tmp = datetime.datetime(int(tokens[2]), int(tokens[0]), int(tokens[1]), int(tokens[3]), int(tokens[4]), int(tokens[5]))
            r['dateOfCreation'] = tmp
            r['dateOfCreationInInt'] = str(int(tokens[2] + tokens[0] + tokens[1] + tokens[3] + tokens[4] + tokens[5]))

        if r['lastUpdated'] is not None and r['lastUpdated'] != '':
            tokens = re.split('[/: ]', r['lastUpdated'])
            tmp = datetime.datetime(int(tokens[2]), int(tokens[0]), int(tokens[1]), int(tokens[3]), int(tokens[4]), int(tokens[5]))
            r['lastUpdated'] = tmp
            r['lastUpdatedInInt'] = str(int(tokens[2] + tokens[0] + tokens[1] + tokens[3] + tokens[4] + tokens[5]))
        
        print(r)
        history.update_one({'_id': r['_id']}, {'$set': r})

