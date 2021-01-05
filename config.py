import os

class DefaultConfig:
    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "acd7d960-9873-4c5c-8ce5-2b11285d182b")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "]Xb&_g&&P%us]*h8c^7yD#b@F=}6")
    
    QNA_KNOWLEDGEBASE_ID = os.environ.get("QnAKnowledgebaseId", "f7c656b6-1908-4076-90e0-b0939e2c9a56")
    QNA_ENDPOINT_KEY = os.environ.get("QnAEndpointKey", "117bfae5-92ad-4c4a-b499-eb237bf07733")
    QNA_ENDPOINT_HOST = os.environ.get("QnAEndpointHostName", "https://rgencuesta.azurewebsites.net/qnamaker")

    #DESPACHADOR LUIS
    #LUIS_APP_ID = os.environ.get("LuisAppId", "162db44c-3212-4c65-bd7c-8ddb6f16e59d")
    #LUIS_API_KEY = os.environ.get("LuisAPIKey", "4989ed1c95d1457ca55331bbb1bd43a0")
    #LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "westus.api.cognitive.microsoft.com/")
    
    LUIS_APP_ID = os.environ.get("LuisAppId", "c5542a02-f85e-4a21-89f7-f93de7deff00")
    LUIS_API_KEY = os.environ.get("LuisAPIKey", "4989ed1c95d1457ca55331bbb1bd43a0")
    LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "westus.api.cognitive.microsoft.com/")