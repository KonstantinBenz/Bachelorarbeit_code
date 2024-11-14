from asyncua import Client, ua
from typing import Any, Optional, Dict
import os
from src.Machine import Machine

# Import logging
from src.loggingConfig import logger

class OPCUA:
    def __init__(self) -> None:
        """
        Initialize the OPCUA instance, managing active subscriptions.
        """
        self.subscriptions = {}

    async def checkSubscription(self, ipAddress: str) -> bool:
        """
        Check if a subscription exists for a given IP address.

        :param ipAddress: IP address of the OPC UA server.
        :return: True if the subscription exists, False otherwise.
        """
        return ipAddress in self.subscriptions

    async def createSubscription(
        self, 
        machine: Machine, 
        interval: int = 2000
    ) -> Optional[Dict[str, Any]]:
        """
        Create a subscription to an OPC UA server for a specific machine, with optional TLS and authentication.

        :param machine: The machine object containing information like IP address, node ID, and OPC UA credentials.
        :param interval: The subscription interval in milliseconds (default: 2000ms).
        :return: A dictionary containing the client, subscription, and handle if successful, None otherwise.
        """
        if await self.checkSubscription(machine.ipAddress):
            logger.info(f"Subscription already exists for {machine.ipAddress}")
            return self.subscriptions[machine.ipAddress]

        try:
            # Create the OPC UA client and connect to the server
            client = Client(f"opc.tcp://{machine.ipAddress}")

            # Use TLS certificates if enabled
            if machine.machineOpcUseCert:
                tls_cert_path = os.getenv('OPCUA_CERT_PATH', './certs/client_cert.pem')
                tls_key_path = os.getenv('OPCUA_KEY_PATH', './certs/client_key.pem')
                client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{tls_cert_path},{tls_key_path}")
                logger.info(f"Using TLS with cert: {tls_cert_path} and key: {tls_key_path}")

            # Use username/password if provided
            if machine.machineOpcUser != "" and machine.machineOpcPass != "":
                client.set_user(machine.machineOpcUser)
                client.set_password(machine.machineOpcPass)
                logger.info(f"Using username/password for {machine.ipAddress}")

            await client.connect()
            logger.info(f"Connected to OPC UA server at {machine.ipAddress}")

            # Create a subscription with a specified interval
            subscription = await client.create_subscription(interval, machine)

            # Subscribe to the specified node
            node = client.get_node(machine.fromNodeID)
            handle = await subscription.subscribe_data_change(node)

            # Store the subscription and client for later use
            self.subscriptions[machine.ipAddress] = {
                "client": client,
                "subscription": subscription,
                "handle": handle,
            }

            logger.info(f"Subscription created for {machine.ipAddress} with interval {interval}ms")
            return self.subscriptions[machine.ipAddress]

        except Exception as e:
            logger.error(f"Failed to create subscription for {machine.ipAddress}: {e}")
            return None

    async def unsubscribe(self, ipAddress: str) -> bool:
        """
        Unsubscribe and disconnect from the OPC UA server at the given IP address.

        :param ipAddress: IP address of the OPC UA server.
        :return: True if successful, False otherwise.
        """
        if not await self.checkSubscription(ipAddress):
            logger.info(f"No subscription exists for {ipAddress}")
            return False

        try:
            # Retrieve the subscription and client
            sub_info = self.subscriptions.pop(ipAddress)
            subscription = sub_info["subscription"]
            client = sub_info["client"]

            # Unsubscribe and delete the subscription
            await subscription.delete()

            # Disconnect the client
            await client.disconnect()

            logger.info(f"Unsubscribed and disconnected from {ipAddress}")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe from {ipAddress}: {e}")
            return False

    async def sendString(self, machine: Machine, value: str) -> bool:
        """
        Send a string value to a specific node on the OPC UA server for a given machine.

        :param machine: The machine object containing information like IP address, node ID, and OPC UA credentials.
        :param value: The string value to be sent to the OPC UA node.
        :return: True if successful, False otherwise.
        """
        try:
            client = self.subscriptions[machine.ipAddress]["client"]

            # Get the node to which the string will be written
            node = client.get_node(machine.fromNodeID)

            # Send the string value to the node
            await node.write_value(ua.Variant(value, ua.VariantType.String))

            logger.info(f"Successfully sent string value '{value}' to node {machine.fromNodeID} on {machine.ipAddress}")
            return True

        except Exception as e:
            logger.error(f"Failed to send string value '{value}' to {machine.fromNodeID} on {machine.ipAddress}: {e}")
            return False

        finally:
            # If the client was created temporarily, disconnect it
            if not await self.checkSubscription(machine.ipAddress):
                await client.disconnect()
                logger.info(f"Disconnected temporary client for {machine.ipAddress}")
