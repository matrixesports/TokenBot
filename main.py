from Bot_Prod import runBotProd
from Bot_Staging import runBotStaging
import os

ZEET_ENVIRONMENT = os.getenv('ZEET_ENVIRONMENT')


if ZEET_ENVIRONMENT == "master":
    runBotProd()
else:
    runBotStaging()



