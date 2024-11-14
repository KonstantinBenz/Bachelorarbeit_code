import asyncio
import logging
import keyboard  # Import the keyboard module
import random  # To randomly select a question
import json  # To load the JSON data from a file
from asyncua import Server, ua
from asyncua.common.methods import uamethod
import os  # For file path handling

# Function to load the JSON data from the file
def load_json_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to randomly select a question from the JSON
def get_random_question(json_data):
    return random.choice(json_data)["question"]

@uamethod
def func(parent, value):
    return value * 2

async def main():
    _logger = logging.getLogger(__name__)

    # Load JSON data from rag_test_results.json
    json_file_path = os.path.join(os.path.dirname(__file__), 'rag_test_results.json')
    json_data = load_json_file(json_file_path)

    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://127.0.0.1:4840/")

    # set up our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # populating our address space
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "fehlercode", "Starting question...")  # Initial string value
    await myvar.set_writable()

    # Set a method, if needed
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),  
        ua.QualifiedName("ServerMethod", idx),
        func,
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    
    _logger.info("Starting server!")

    # Server loop
    async with server:
        while True:
            await asyncio.sleep(1)  # Check more frequently
            if keyboard.is_pressed('e'):
                # Select a random question
                random_question = get_random_question(json_data)
                _logger.info("Set value of %s to new question: %s", myvar, random_question)
                await myvar.write_value(random_question)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(), debug=False)
