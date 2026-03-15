from .config import settings

class Endpoints:
    def __init__(self):
        self.base_url = f"{settings.ADGUARD_BASE_URL}:{settings.ADGUARD_PORT}"
        self.prefix = '/control'
        self.url = f"{self.base_url}{self.prefix}"

    #Querylog
    QUERYLOG = "/querylog?&response_status=all&limit={limit}{oldest}"

    #Status
    FILTERING = "/filtering/status"
    SET_FILTERING = '/filtering/set_rules'

    #Profile
    PROFILE = "/profile"

    def get_url(self, endpoint: str, **kwargs) -> str:
        """Create full URL"""
        url = f"{self.url}{endpoint}"
        for key, value in kwargs.items():
            url = url.replace(f"{{{key}}}", str(value))
        return url

endpoints = Endpoints()