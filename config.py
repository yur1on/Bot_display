# tok = "6719595706:AAFbFJCJaB10rqwri7x_3WAuwvFSNLUtNDE"
# # tok = "5851318234:AAETu8A7RmnNXdrUbVABoUqMe4c_8cSSlpw"
#
# ADMIN_ID = 486747175
# # 6719595706:AAFbFJCJaB10rqwri7x_3WAuwvFSNLUtNDE
# # token_p2p: str = "4100118591872654.47CCFCCFE3287C452BF2FD569497BE0FAA3B9D3B2E84BD7506DA497112CD40F0E9F836B1858623C80E1320F935AED3363D68157525FFBDF8A38BC04057DA93AD5C7102E304B233425E8CB4A4A3D59E2950B44317CE6667E88498329B3CA6FBCC71C01F20E3D953C138EFB7AD99A069887372C208CE746426D4998FC5FAEE7230"
#
# WEBAPP_URL = "https://yur1on.github.io/tg-size-webapp/"

# config.py
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "user_database.db"

# токен: по-хорошему хранить в env, но пока оставим как есть
tok = os.getenv("BOT_TOKEN", "6719595706:AAFbFJCJaB10rqwri7x_3WAuwvFSNLUtNDE")
# tok = os.getenv("BOT_TOKEN", "6836113072:AAFdU2EZAOyEsCqCSrelFnR1DR9wEpoICAs")
ADMIN_ID = 486747175
WEBAPP_URL = "https://yur1on.github.io/tg-size-webapp/"

# лог для старта
print("🗄 Using DB:", DB_PATH)





