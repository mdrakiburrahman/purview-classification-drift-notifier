from azure.purview.catalog import PurviewCatalogClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from pprint import *
import os
import json
import sys
import jmespath
from datetime import datetime

# Fill up based on business logic, can be Custom Classifications as well
ClassificationMap = {
    "MICROSOFT.PERSONAL.NAME": ["Contoso_IC_Confidential", "0"],
    "MICROSOFT.PERSONAL.US.PHONE_NUMBER": ["Contoso_IC_Confidential", "0"],
    "MICROSOFT.PERSONAL.EMAIL": ["Contoso_IC_Confidential", "0"],
    "MICROSOFT.FINANCIAL.CREDIT_CARD_NUMBER": ["Contoso_IC_Sensitive", "1"],
    "MICROSOFT.GOVERNMENT.US.SOCIAL_SECURITY_NUMBER": ["Contoso_IC_Sensitive", "1"]
}

class RecvService:
    def __init__(self):
        self.CatalogClient = self.authenticate()
        
    def authenticate(self):
        account_endpoint = "https://{}.purview.azure.com".format(os.getenv('PURVIEW_NAME'))
        credential = DefaultAzureCredential()
        catalog_client = PurviewCatalogClient(endpoint=account_endpoint, credential=credential)
        return catalog_client

    def printer(self, RequestType, payload):
        print("\n" + "="*len(RequestType) + "\n" +
                "{}".format(RequestType) + "\n" +
                "="*len(RequestType) + "\n" +
                json.dumps(payload, indent=4, sort_keys=True) + "\n",
                file=sys.stderr)

    def classificationAddedOrUpdated(self, payload):
        self.printer("Classification Added", payload)
        guid = payload["message"]["entity"]["guid"]
        response = self.getColumnDetails(guid)

        # Guid was deleted, return immediately
        try:
            if response["errorCode"]:
                 self.printer("Purview Response", response["errorMessage"])
                 return None
        except:
            pass # No error code; continue

        # Parse out response for relevant details
        columnDetails = self.parseColumnDetails(response)

        print("Column Name: " + columnDetails["columnName"])
        print("Qualified Name: " + columnDetails["qualifiedName"])
        print("Data Type: " + columnDetails["columnDataType"])
        print("Purview Classified As: " + columnDetails["columnClassificationType"])
        print("Resulting Sensitivity: " + columnDetails["resultSensitivity"])
        print("Declared Sensitivity: " + columnDetails["declaredSensitivity"])
        print("Current Encryption Type: " + columnDetails["currentEncryptionType"])
        print("Desired Encryption Type: " + columnDetails["desiredEncryptionType"])
        print("Update Time: " + columnDetails["updateTime"])
    
    def getColumnDetails(self, guid):
        # Get detailed information about an asset
        cmd = "pv entity readBulk --guid {}".format(guid)
        stream = os.popen(cmd)
        response = json.loads(stream.read())
        return response

    def parseColumnDetails(self, payload):
        return {
                    "columnName" : payload["entities"][0]["attributes"]["name"],
                    "qualifiedName" : payload["entities"][0]["attributes"]["qualifiedName"],
                    "columnDataType" : payload["entities"][0]["attributes"]["data_type"],
                    "columnClassificationType" : payload["entities"][0]["classifications"][0]["typeName"],
                    "resultSensitivity" : ClassificationMap[payload["entities"][0]["classifications"][0]["typeName"]][0],
                    "declaredSensitivity" : payload["entities"][0]["relationshipAttributes"]["meanings"][0]["displayText"],
                    "currentEncryptionType" : str(payload["entities"][0]["attributes"]["encryptionType"]),
                    "desiredEncryptionType" : ClassificationMap[payload["entities"][0]["classifications"][0]["typeName"]][1],
                    "updateTime" : str(datetime.utcfromtimestamp(payload["entities"][0]["updateTime"]/1000).strftime('%Y-%m-%d %H:%M:%S'))
                }