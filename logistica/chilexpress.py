import requests
from django.conf import settings

class ChilexpressAPI:
    def __init__(self):
        self.api_key = settings.CHILEXPRESS_API_KEY
        self.environment = settings.CHILEXPRESS_ENVIRONMENT
        
        # Chilexpress tiene URLs distintas para pruebas y producción
        if self.environment == 'PROD':
            self.base_url = "https://services.chilexpress.cl/api/v1"
        else:
            self.base_url = "https://testservices.chilexpress.cl/api/v1"

        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def probar_conexion(self):
        """
        Hace una petición básica para verificar regiones y probar 
        que nuestra API Key está funcionando.
        """
        endpoint = f"{self.base_url}/georeference/api/v1.0/regions"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status() # Lanza error si el status no es 200
            
            data = response.json()
            return {
                "status": "success",
                "data": data.get('regions', [])
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e)
            }