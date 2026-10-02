import requests

from agent import FruitAgent, MODEL
from inventory import INVENTORY_PATH, load_inventory


def main():
    try:
        load_inventory()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Cannot load inventory: {error}")
        return

    agent = FruitAgent()

    print("Local Fruit Store Agent")
    print(f"Model: {MODEL}")
    print(f"Inventory file: {INVENTORY_PATH}")
    print("Prices are in USD. Quantities are in kilograms.")
    print()
    print("Commands:")
    print("  confirm order - Complete the pending order")
    print("  cancel order  - Discard the pending order")
    print("  reset         - Clear memory and the pending order")
    print("  exit          - Close the application")

    while True:
        try:
            user_text = input("\nYou: ").strip()

            if not user_text:
                continue

            if user_text.casefold() in {"exit", "quit"}:
                print("Goodbye!")
                break

            if user_text.casefold() == "reset":
                agent.reset()
                print("Memory and pending order cleared.")
                print("Inventory is unchanged.")
                continue

            answer = agent.ask(user_text)
            print(f"\nAgent: {answer}")

        except requests.ConnectionError:
            print(
                "Cannot connect to Ollama. "
                "Make sure Ollama is running."
            )

        except requests.Timeout:
            print("The local model timed out. Please try again.")

        except requests.HTTPError as error:
            print(f"Ollama request failed: {error}")
            print(f"Install the model with: ollama pull {MODEL}")

        except (ValueError, KeyError, TypeError) as error:
            print(f"Invalid model response or inventory data: {error}")

        except OSError as error:
            print(f"File operation failed: {error}")

        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()