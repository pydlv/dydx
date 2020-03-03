from dydx.client import Client

with open("pk.txt", "r") as f:
    pk = f.read().strip()

# create a new client with a private key (string or bytearray)
client = Client(
    private_key=pk,
    node='https://parity.expotrading.com'
)

public_address = client.public_address