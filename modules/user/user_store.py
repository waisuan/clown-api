from datetime import date


class UserStore:
    _instance = None

    def __init__(self):
        self.storage = {}

    def store(self, user, token):
        self.storage[user] = {'token': token, 'date': date.today()}

    def purge(self, user):
        self.storage.pop(user, None)

    def contains(self, user, token):
        return (user in self.storage) and (
            self.storage[user]['token'] == token)

    def purgeStaleUsers(self):
        today = date.today()
        for user, value in self.storage.items():
            if (today - value['date']).days >= 7:
                print("Removing ", user, " from user store...")
                self.purge(user)
