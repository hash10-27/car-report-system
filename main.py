import threading
from web_app import app

def run_server():
    app.run(host="127.0.0.1", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_server).start()

    # إبقاء التطبيق شغال
    import time
    while True:
        time.sleep(1)