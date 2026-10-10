import requests  # Handle HTTP request errors.

from agent import FruitAgent, MODEL  # Import the agent and model name.
from inventory import INVENTORY_PATH, load_inventory  # Import inventory settings and loader.


def main():  # Run the application.
    try:  # Try loading the inventory.
        load_inventory()  # Check that inventory can load.
    except (OSError, ValueError, KeyError, TypeError) as error:  # Catch inventory errors.
        print(f"Cannot load inventory: {error}")  # Display the error.
        return  # Stop the application.

    agent = FruitAgent()  # Create the fruit store agent.

    print("Local Fruit Store Agent")  # Display the application title.
    print(f"Model: {MODEL}")  # Display the model name.
    print(f"Inventory file: {INVENTORY_PATH}")  # Display the inventory path.
    print("Prices are in USD. Quantities are in kilograms.")  # Explain prices and units.
    print()  # Print a blank line.
    print("Commands:")  # Display the commands heading.
    print("  confirm order - Complete the pending order")  # Explain order confirmation.
    print("  cancel order  - Discard the pending order")  # Explain order cancellation.
    print("  reset         - Clear memory and the pending order")  # Explain resetting.
    print("  exit          - Close the application")  # Explain exiting.

    while True:  # Keep accepting user messages.
        try:  # Handle input and possible errors.
            user_text = input("\nYou: ").strip()  # Read input and trim whitespace.

            if not user_text:  # Check for empty input.
                continue  # Ask for input again.

            if user_text.casefold() in {"exit", "quit"}:  # Check exit commands without case.
                print("Goodbye!")  # Display the goodbye message.
                break  # Leave the conversation loop.

            if user_text.casefold() == "reset":  # Check the reset command.
                agent.reset()  # Clear agent memory and pending order.
                print("Memory and pending order cleared.")  # Confirm the reset.
                print("Inventory is unchanged.")  # Explain that stock is unchanged.
                continue  # Ask for input again.

            answer = agent.ask(user_text)  # Send the message to the agent.
            print(f"\nAgent: {answer}")  # Display the agent's answer.

        except requests.ConnectionError:  # Catch connection failures.
            print("Cannot connect to Ollama. Make sure Ollama is running.")  # Explain the connection problem.

        except requests.Timeout:  # Catch request timeouts.
            print("The local model timed out. Please try again.")  # Suggest trying again.

        except requests.HTTPError as error:  # Catch HTTP response errors.
            print(f"Ollama request failed: {error}")  # Display the request error.
            print(f"Install the model with: ollama pull {MODEL}")  # Show the installation command.

        except (ValueError, KeyError, TypeError) as error:  # Catch invalid data errors.
            print(f"Invalid model response or inventory data: {error}")  # Display the data error.

        except OSError as error:  # Catch file operation errors.
            print(f"File operation failed: {error}")  # Display the file error.

        except (EOFError, KeyboardInterrupt):  # Handle closed input or Ctrl+C.
            print("\nGoodbye!")  # Display the goodbye message.
            break  # Leave the conversation loop.


if __name__ == "__main__":  # Run only when executed directly.
    main()  # Start the application.
