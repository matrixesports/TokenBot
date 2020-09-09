from Bot_Prod import runBotProd
from Bot_Staging import runBotStaging
import os
from datetime import date
from DBBackup import upload_to_aws


ZEET_ENVIRONMENT = os.getenv('ZEET_ENVIRONMENT')

local_file = "/data/discord-commerce.db"
bucket_name = "matrixdatabasebackup"
s3_file_name = str(date.today())

uploaded = upload_to_aws('local_file', 'bucket_name', 's3_file_name')

if ZEET_ENVIRONMENT == "master":
    runBotProd()
else:
    runBotStaging()



