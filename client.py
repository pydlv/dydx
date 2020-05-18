from dydx.client import Client

with open("pk.txt", "r") as f:
    pk = f.read().strip()

# create a new client with a private key (string or bytearray)
client = Client(
    private_key=pk,
    node='https://mainnet.infura.io/v3/a2aaf96061254e0ab5dcfc3005a8a379'
)

public_address = client.public_address