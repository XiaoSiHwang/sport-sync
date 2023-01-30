class GarminCookie():

    id = None

    def __init__(self, main_email, main_auth_domain, sync_email, sync_auth_domain):
        self.main_email = main_email
        self.main_auth_domain = main_auth_domain
        self.sync_email = sync_email
        self.sync_auth_domain = sync_auth_domain
        self.id

    def get_id(self):
        return self.id

    def set_id(self,id):
        self.id=id