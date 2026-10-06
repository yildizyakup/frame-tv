"""First-time pairing with the Frame TV: accept the prompt on the TV screen and the token is saved."""
import os
import warnings

from samsungtvws import SamsungTVWS

from i18n import t
from upload import HOST, TOKEN_FILE

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

tv = SamsungTVWS(host=HOST, port=8002, token_file=TOKEN_FILE, name="Claude", timeout=60)
tv.open()
print(t("connect_ok", saved=os.path.exists(TOKEN_FILE)))

art = tv.art()
print(t("connect_supported", value=art.supported()))
print(t("connect_artmode", value=art.get_artmode()))
print(t("connect_current", value=art.get_current().get("content_id")))
print(t("connect_count", value=len(art.available())))
tv.close()
