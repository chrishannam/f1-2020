from typing import NamedTuple
from f1_2020_telemetry.types import TrackIDs

from cassandra.connectors.influxdb import InfluxDBConnector
from cassandra.telemetry.constants import PACKET_MAPPER
from cassandra.telemetry.source import Feed
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class Race(NamedTuple):
    circuit: str
    total_laps: int


def main():
    race_details = None

    influx_conn = InfluxDBConnector(host="192.168.0.101")
    logger.info("Starting server to receive telemetry data.")
    feed = Feed()
    lap_number = 1

    while True:
        packet = feed.get_latest()

        if not packet:
            continue

        data = []
        if packet["type"] == "PacketSessionData_V1" and not race_details:
            race_details = Race(
                circuit=TrackIDs[packet["trackId"]], total_laps=packet["totalLaps"]
            )

        # we are late, so spin until we find out which race we are at
        if not race_details:
            continue

        if packet["type"] == "PacketLapData_V1":
            lap_number = packet["currentLapNum"]

        if packet["type"] in PACKET_MAPPER.keys():
            for name, value in packet.items():
                if name in ["type", "mfdPanelIndex", "buttonStatus"]:
                    continue

                # drivers name are bytes
                if name == "name" and packet["type"] == "PacketParticipantsData_V1":
                    if type(value) == bytes:
                        value = value.decode("utf-8")

                data.append(
                    {
                        "measurement": name,
                        "tags": {
                            "type": packet["name"],
                            "track": race_details.circuit,
                            "lap": lap_number,
                            "total_laps": race_details.total_laps,
                        },
                        "fields": {"value": value},
                    }
                )
                sequence = ["mem,host=host1 used_percent=23.43234543",
                            "mem,host=host1 available_percent=15.856523"]

            influx_conn.write(sequence)


if __name__ == "__main__":
    main()
