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
            '_id': 0,
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
        return helpr.clean_single_machine_for_read(machines.find_one({'serialNumber': id}, self.query_projections) or {})

    def _get_due_machines(self):
        machines = self.db.machines
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        due_today = machines.find({'ppmDate': today}, self.query_project_id_only)
        return helpr.flatten_list(due_today, 'serialNumber')

    def _get_overdue_machines(self):
        machines = self.db.machines
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        two_weeks_ago = today + datetime.timedelta(days=-14)
        overdue = machines.find({'ppmDate': {'$gte': two_weeks_ago, '$lt': today}}, self.query_project_id_only)
        return helpr.flatten_list(overdue, 'serialNumber')

    def _get_almost_due_machines(self):
        machines = self.db.machines
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        two_weeks_from_today = today + datetime.timedelta(days=14)
        almost_due = machines.find({'ppmDate': {'$gt': today, '$lte': two_weeks_from_today}}, self.query_project_id_only)
        return helpr.flatten_list(almost_due, 'serialNumber')

    def get_machines_with_ppm_status(self):
        return self._get_due_machines() + self._get_almost_due_machines() + self._get_overdue_machines()
        # {'count': results.count(), 'data': helpr.clean_for_read(list(results))}
        #return {'due': helpr.clean_for_read(list(due_today)), 'almost': helpr.clean_for_read(list(almost_due)), 'over': helpr.clean_for_read(list(overdue))}

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


if __name__ == "__main__":
    mgr = DatabaseManager('mongodb://localhost:27017/', 'emblem')
    result = mgr.get_machines_with_ppm_status()
    for machine in result:
        print(machine)
    # result = mgr.get_machines(None, None, None, None)
    # for r in result['data']:
    #     mgr.update_machine(r['serialNumber'], {'ppmStatus': ''})

