"""First-time pairing with the Frame TV: accept the prompt on the TV screen and the token is saved.

Usage: connect.py [TV IP address]   (the address is remembered in settings.json)
"""
import os
import sys
import warnings

from samsungtvws import SamsungTVWS

from i18n import save_setting, t
from upload import HOST, TOKEN_FILE

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

host = sys.argv[1] if len(sys.argv) > 1 else HOST
if not host:
    sys.exit(t("need_host"))
save_setting("host", host)

tv = SamsungTVWS(host=host, port=8002, token_file=TOKEN_FILE, name="Claude", timeout=60)
tv.open()
print(t("connect_ok", saved=os.path.exists(TOKEN_FILE)))

art = tv.art()
print(t("connect_supported", value=art.supported()))
print(t("connect_artmode", value=art.get_artmode()))
print(t("connect_current", value=art.get_current().get("content_id")))
print(t("connect_count", value=len(art.available())))
tv.close()
