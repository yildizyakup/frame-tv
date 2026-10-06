"""Frame TV'ye ilk bağlantı: TV ekranındaki izin isteği onaylanınca token kaydedilir."""
import os
from samsungtvws import SamsungTVWS

HOST = "192.168.1.104"
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tv-token.txt")

tv = SamsungTVWS(host=HOST, port=8002, token_file=TOKEN_FILE, name="Claude", timeout=60)
tv.open()
print("Bağlantı OK, token:", os.path.exists(TOKEN_FILE))

art = tv.art()
print("Sanat Modu destekleniyor:", art.supported())
print("Sanat Modu açık mı:", art.get_artmode())
current = art.get_current()
print("Şu an gösterilen eser:", current.get("content_id"))
print("Yüklü eser sayısı:", len(art.available()))
tv.close()
