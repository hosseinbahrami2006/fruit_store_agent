# Local Fruit Store Agent

An educational agent powered by local Ollama and qwen2.5:3b.

## Requirements

- Python 3.10 or newer
- Ollama
- The qwen2.5:3b model

## Setup

Install the model:

```bash
ollama pull qwen2.5:3b
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Make sure Ollama is running. If necessary, start it with:

```bash
ollama serve
```

Run the application:

```bash
python main.py
```

Alternatively, open main.py in VSCode and click Run.

## Example Requests

- Which fruits are available?
- What is the price of apples?
- Calculate an invoice for 2 kg of apples and 3 kg of bananas.
- Add one more kilogram of apples.
- Calculate an invoice for 100 kg of apples.

## Commands

- confirm order: Confirm the pending order and reduce inventory.
- cancel order: Discard the pending order without changing inventory.
- reset: Clear conversation memory and the pending order.
- exit: Close the application.

Confirmation commands are case-insensitive.

## Architecture

- main.py: Console interface.
- agent.py: Model communication, action selection, state, and memory.
- tools.py: Tool definitions and order confirmation.
- calculator.py: Exact decimal invoice arithmetic.
- inventory.py: JSON reading, validation, and atomic saving.
- fruits.json: Persistent product inventory.

The agent uses JSON-based action selection rather than native
Ollama tool calling. Python validates and executes the chosen action.

## Order Workflow

1. The user requests an invoice quote.
2. The calculator tool reads current prices and validates the basket.
3. If any item exceeds stock, the entire quote is rejected.
4. A successful quote becomes the pending order.
5. The user types confirm order.
6. The application checks current stock and prices again.
7. If all checks pass, stock is reduced and saved to fruits.json.
8. The pending order is cleared to prevent duplicate confirmation.

A new quote replaces the previous pending order.

An invalid basket clears the previous pending order.

Quotes do not reserve inventory.

## Persistence

Inventory changes persist in fruits.json.

Conversation memory and pending orders exist only during the
current application session.

Confirmed-order history is not stored in this version.

## Limitations

This is a single-user, single-process educational application.

Atomic file replacement prevents partial JSON writes, but it does
not provide concurrency control between multiple running instances.
Do not run multiple instances against the same inventory file.

The local model can misinterpret natural-language requests.
Review the displayed products and quantities before confirmation.

This application does not process payments.