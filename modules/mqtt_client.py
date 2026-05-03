"""MQTT IoT Entegrasyonu — Gerçek İnverter Verisi

Gerçek veya simüle edilmiş bir MQTT broker'dan inverter telemetri verisi okur.
Desteklenen: SMA, Huawei SUN2000, Growatt, Fronius (standart MQTT topic yapısı)

Bağlantı yoksa veya broker çevrimdışıysa simülasyon modu devreye girer.

Kurulum: pip install paho-mqtt
"""

import time
import json
import threading
import numpy as np
from datetime import datetime
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False


# ─── Varsayılan MQTT Topic Şeması ─────────────────────────────────────────────
# solar/<inverter_id>/power     → anlık güç (W)
# solar/<inverter_id>/energy    → günlük enerji (kWh)
# solar/<inverter_id>/voltage   → DC gerilimi (V)
# solar/<inverter_id>/temp      → panel sıcaklığı (°C)
# solar/<inverter_id>/status    → durum (online/fault/idle)


class MQTTInverterClient:
    """
    MQTT broker'a bağlanıp gerçek zamanlı inverter telemetrisi alır.
    Simülasyon modu otomatik devreye girer.
    """

    def __init__(self, broker="localhost", port=1883,
                 inverter_id="inv001", username=None, password=None):
        self.broker       = broker
        self.port         = port
        self.inverter_id  = inverter_id
        self.username     = username
        self.password     = password

        self._latest: dict = {}
        self._history: list = []
        self._connected = False
        self._client: Optional[object] = None
        self._sim_thread: Optional[threading.Thread] = None
        self._sim_running = False

    # ── Bağlantı ──────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Broker'a bağlan. Başarısız olursa simülasyon başlat."""
        if not MQTT_AVAILABLE:
            self._start_simulation()
            return False

        try:
            self._client = mqtt.Client(client_id=f"f2a_{self.inverter_id}")
            if self.username:
                self._client.username_pw_set(self.username, self.password)

            self._client.on_connect    = self._on_connect
            self._client.on_message    = self._on_message
            self._client.on_disconnect = self._on_disconnect

            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()
            time.sleep(1.5)  # bağlantı için bekle

            if self._connected:
                return True
            else:
                self._client.loop_stop()
                self._start_simulation()
                return False
        except Exception:
            self._start_simulation()
            return False

    def disconnect(self):
        """Bağlantıyı kapat."""
        self._sim_running = False
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    # ── Veri Okuma ────────────────────────────────────────────────────────────

    def get_latest(self) -> dict:
        """En güncel telemetri verisini döndür."""
        return dict(self._latest)

    def get_history(self, n: int = 60) -> list:
        """Son n ölçümün geçmişini döndür."""
        return self._history[-n:]

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_simulated(self) -> bool:
        return self._sim_running

    # ── MQTT Callback'leri ────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            base = f"solar/{self.inverter_id}/#"
            client.subscribe(base)
        else:
            self._connected = False

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode("utf-8"))
            key = topic.split("/")[-1]
            self._latest[key] = payload
            self._latest["timestamp"] = datetime.now().isoformat()
            self._append_history()
        except Exception:
            pass

    # ── Simülasyon Modu ───────────────────────────────────────────────────────

    def _start_simulation(self):
        """Gerçek broker yoksa fizik tabanlı simülasyon."""
        self._sim_running = True
        self._connected = False
        self._sim_thread = threading.Thread(
            target=self._sim_loop, daemon=True
        )
        self._sim_thread.start()

    def _sim_loop(self):
        rng = np.random.RandomState(42)
        while self._sim_running:
            h = datetime.now().hour
            # Gündüz profili
            if 6 <= h <= 19:
                angle = np.sin((h - 6) * np.pi / 13)
                base_power = max(0, 5000 * angle)  # W (5 kW panel)
                noise = rng.randn() * 200
                power_w = max(0, base_power + noise)
            else:
                power_w = 0.0

            self._latest = {
                "power":     round(power_w, 1),          # W
                "power_kw":  round(power_w / 1000, 3),   # kW
                "energy":    round(power_w * 0.25 / 1000, 3),  # kWh (15 dk)
                "voltage":   round(rng.uniform(380, 420), 1),  # V
                "temp":      round(25 + 0.03 * power_w / 1000 + rng.randn(), 1),
                "status":    "online" if power_w > 0 else "idle",
                "timestamp": datetime.now().isoformat(),
                "simulated": True,
            }
            self._append_history()
            time.sleep(5)

    def _append_history(self):
        entry = dict(self._latest)
        entry["recorded_at"] = datetime.now().isoformat()
        self._history.append(entry)
        # Son 1440 kayıt (24 saat × 60 dk) tut
        if len(self._history) > 1440:
            self._history.pop(0)


# ─── Singleton bağlantı yöneticisi ────────────────────────────────────────────

_client_instance: Optional[MQTTInverterClient] = None


def get_mqtt_client(broker="localhost", port=1883,
                    inverter_id="inv001",
                    username=None, password=None) -> MQTTInverterClient:
    """Singleton MQTT istemcisi — Streamlit session boyunca tek bağlantı."""
    global _client_instance
    if _client_instance is None:
        _client_instance = MQTTInverterClient(
            broker=broker, port=port,
            inverter_id=inverter_id,
            username=username, password=password,
        )
        _client_instance.connect()
    return _client_instance


def reset_mqtt_client():
    """Bağlantıyı sıfırla (ayarlar değiştiğinde)."""
    global _client_instance
    if _client_instance:
        _client_instance.disconnect()
    _client_instance = None
