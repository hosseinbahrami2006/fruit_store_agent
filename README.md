# Local Fruit Store Agent

A local fruit-store assistant built with **LangChain**, **LangGraph**, and **Ollama**.

The assistant answers questions about fruit prices and stock, prepares invoice quotes, and updates inventory only after an explicit order confirmation.

Inventory validation, invoice calculations, and stock updates are handled by Python code—not by the language model.
 
## Features

- Run a local language model through Ollama.
- Manage the agent workflow with LangGraph.
- List available fruits, prices, and stock.
- Look up individual products.
- Create invoice quotes for complete baskets.
- Modify a pending basket using conversational follow-up requests.
- Combine duplicate products before validating stock.
- Normalize common plural fruit names.
- Use `Decimal` for price and quantity calculations.
- Reject the entire invoice if any basket item is invalid.
- Require an explicit `confirm order` command before updating inventory.
- Revalidate stock, prices, and currency during confirmation.
- Keep the latest 10 conversation turns in memory.
- Limit each request to 8 model-decision rounds.
- Save inventory using atomic file replacement.

## Technology Stack

| Component | Purpose |
|---|---|
| Python | Application logic |
| LangChain / `ChatOllama` | Communication with the local model |
| LangGraph | Agent workflow and routing |
| Ollama | Local model server |
| Qwen 2.5 3B | Default language model |
| JSON | Inventory storage |
| Decimal | Exact decimal arithmetic |

## Project Structure

```text
fruit_store_agent/
├── agent.py
├── calculator.py
├── inventory.py
├── tools.py
├── main.py
├── fruits.json
├── requirements.txt
└── README.md
```

### `agent.py`

Defines the `FruitAgent` class and the LangGraph workflow.

Responsibilities include:

- Connecting to Ollama through `ChatOllama`.
- Parsing JSON decisions returned by the model.
- Routing decisions to existing Python tools.
- Managing conversation memory and the pending order.
- Handling confirmation and cancellation commands.
- Returning calculator-generated invoices directly.
- Translating connection and HTTP errors into exception types handled by `main.py`.

### `inventory.py`

Loads, validates, and saves the inventory.

It also:

- Normalizes product names.
- Validates numeric values.
- Combines duplicate basket items.
- Checks product availability and stock.
- Replaces the inventory file atomically when saving.

### `calculator.py`

Calculates invoice lines using trusted inventory prices.

Each line subtotal is rounded to two decimal places using `ROUND_HALF_UP`. The total is the sum of the rounded line subtotals.

### `tools.py`

Provides the application tools:

| Function | Purpose |
|---|---|
| `list_products()` | Read all products, prices, and stock |
| `get_product(product_name)` | Read information about one fruit |
| `calculator(items)` | Validate a basket and create a quote |
| `confirm_order(quote)` | Revalidate a quote and reduce stock |
| `format_invoice(quote, confirmed=False)` | Format a quote or confirmed invoice |

Only `list_products`, `get_product`, and `calculator` are available as model-selected actions.

`confirm_order` is called directly by the application when the user enters the confirmation command.

### `main.py`

Provides the command-line interface, initializes the agent, and handles supported commands and errors.

### `fruits.json`

Stores the currency, quantity unit, product names, prices, and available stock.

## Requirements

- Python 3.10 or newer
- Ollama installed and running
- The `qwen2.5:3b` model
- The Python packages listed in `requirements.txt`

An internet connection is needed to install dependencies and download the model. Once installed, the assistant can run locally without a cloud model API key.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/hosseinbahrami2006/fruit_store_agent.git
cd fruit_store_agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

The `requirements.txt` file contains:

```txt
langchain-core
langchain-ollama
langgraph
httpx
requests
```

`requests` remains necessary for compatibility with the existing exception handlers. Model requests are sent through `ChatOllama`, not through `requests.post`.

Standard-library modules such as `json`, `decimal`, `pathlib`, and `typing` do not require separate installation.

### 4. Install Ollama

Download and install Ollama from:

https://ollama.com

### 5. Download the model

```bash
ollama pull qwen2.5:3b
```

### 6. Start Ollama

If Ollama is not already running:

```bash
ollama serve
```

Keep the server running while using the application.

### 7. Start the application

```bash
python main.py
```

## Usage

Ask questions or describe the basket you want to purchase.

Examples:

```text
What fruits do you have?
```

```text
What is the price of apples?
```

```text
How much mango is available?
```

```text
Create an invoice for 2 kg of apples and 3 kg of bananas.
```

```text
Change the apples to 1 kg.
```

```text
Add 2 kg of oranges to the order.
```

Follow-up requests use conversation history and the pending order. Because basket interpretation is model-driven, review each quote before confirming it.

### Commands

| Command | Action |
|---|---|
| `confirm order` | Confirm the pending quote and update inventory |
| `cancel order` | Discard the pending quote without changing inventory |
| `reset` | Clear conversation memory and the pending quote |
| `exit` or `quit` | Close the application |

Commands are case-insensitive, and surrounding whitespace is ignored.

Phrases such as “yes” or “go ahead” do not directly authorize a stock update. Use `confirm order`.

## Example Invoice

For inventory prices of `2.50 USD/kg` for Apple and `1.80 USD/kg` for Banana:

```text
You: Create an invoice for 2 kg of apples and 3 kg of bananas.

Agent: Invoice quote:
- Apple: 2 kg x 2.50 USD/kg = 5.00 USD
- Banana: 3 kg x 1.80 USD/kg = 5.40 USD

Total: 10.40 USD
Stock has not been reserved or reduced.
Type 'confirm order' to complete this order, or 'cancel order' to discard it.
```

After confirmation:

```text
You: confirm order

Agent: Confirmed invoice:
- Apple: 2 kg x 2.50 USD/kg = 5.00 USD
- Banana: 3 kg x 1.80 USD/kg = 5.40 USD

Total: 10.40 USD
Order confirmed. Inventory has been updated.
```

Exact quantity formatting may vary, but prices and totals come from the Python calculator.

## Agent Workflow

Ordinary requests run through the following graph:

```text
START
  |
  v
model
  |
  v
execute_action
  |
  +-- Valid answer --------------------> END
  |
  +-- Valid calculator result ---------> END
  |
  +-- Invalid basket ------------------> END
  |
  +-- Inventory result / action error
          |
          +-- Rounds remaining --------> model
          |
          +-- Round limit reached -----> limit_reached
                                              |
                                              v
                                             END
```

Confirmation and cancellation are handled before entering the graph.

### Graph State

The graph state contains:

| Field | Description |
|---|---|
| `messages` | System instructions, history, user input, and tool results |
| `decision` | The latest JSON decision from the model |
| `rounds` | Number of model calls during the current request |
| `answer` | Final response, or `None` while processing |

Conversation memory and the pending order are stored on the `FruitAgent` instance. They are not persisted between application runs.

### Model Decision Format

The application retains a JSON action protocol rather than using native tool calling through `bind_tools`.

Example decisions:

```json
{
  "action": "get_product",
  "arguments": {
    "product_name": "Apple"
  }
}
```

```json
{
  "action": "calculator",
  "arguments": {
    "items": [
      {
        "product_name": "Apple",
        "quantity_kg": 2
      }
    ]
  }
}
```

```json
{
  "action": "answer",
  "answer": "Which fruit would you like to buy?"
}
```

LangChain handles model communication, while LangGraph controls action execution and routing.

## Inventory Format

`fruits.json` must contain a valid JSON object with this structure:

```json
{
  "currency": "USD",
  "quantity_unit": "kg",
  "products": [
    {
      "name": "Apple",
      "price_per_kg": "2.50",
      "stock_kg": "44"
    },
    {
      "name": "Banana",
      "price_per_kg": "1.80",
      "stock_kg": "34"
    }
  ]
}
```

### Validation Rules

- Currency must be a string.
- The quantity unit must be `kg`.
- Product names must be nonempty strings.
- Product names must be unique after normalization.
- Prices must be finite and greater than zero.
- Stock must be finite and nonnegative.
- Requested quantities must be finite and greater than zero.
- The complete basket must pass validation before an invoice is issued.

Numeric strings are supported and help preserve decimal values.

## Order Lifecycle

1. The user requests a basket.
2. The model sends the complete basket to `calculator`.
3. Python reads trusted inventory prices and validates stock.
4. The calculator creates an invoice quote.
5. The quote becomes the pending order.
6. The user reviews the quote.
7. The user enters `confirm order`.
8. Python reloads the inventory and revalidates the basket.
9. If stock, prices, and currency are still valid, inventory is updated.
10. The pending order is cleared after a successful save.

### Important Behavior

- Quotes do not reserve or reduce stock.
- A new calculator request replaces the previous pending order.
- An invalid replacement basket clears the previous pending order.
- Cancellation and reset do not change inventory.
- Confirmation fails if stock is insufficient or quoted prices or currency have changed.
- On a validation failure during confirmation, the pending order is cleared and a new quote is required.
- The model has no exposed action for updating inventory.

## Configuration

The main settings are in `agent.py`:

```python
MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"

MEMORY_TURNS = 10
MAX_TOOL_ROUNDS = 8
```

`ChatOllama` uses the server base URL derived from `OLLAMA_URL`.

Model generation uses:

- Temperature: `0`
- JSON output mode
- HTTP client timeout: `180` seconds

The inventory path is configured in `inventory.py`:

```python
INVENTORY_PATH = Path(__file__).resolve().parent / "fruits.json"
```

## Troubleshooting

### Cannot connect to Ollama

Make sure Ollama is running:

```bash
ollama serve
```

Check that the configured address is correct.

### Model is not installed

Download the configured model:

```bash
ollama pull qwen2.5:3b
```

### Model request times out

Local generation speed depends on your hardware and available resources.

Close resource-heavy applications, try a compatible smaller model, or adjust the client timeout in `agent.py`.

### Invalid model response

JSON output mode does not guarantee that the model will always return the required action fields.

Try a clearer request or a model that follows structured instructions more reliably.

### Cannot load inventory

Check that:

- `fruits.json` exists next to `inventory.py`.
- The file contains valid JSON.
- Required fields are present.
- Prices and stock satisfy the validation rules.
- The quantity unit is `kg`.

### Insufficient stock

Request a smaller quantity or choose another product. No partial invoice is issued when any basket item fails validation.

## Limitations

- This is a local command-line application, not a production checkout system.
- Inventory saves use atomic replacement, but there is no lock around the full read–validate–write operation. Concurrent processes can cause conflicting updates.
- Conversation memory and pending orders are lost when the application closes.
- Invoice formatting is deterministic, but ordinary natural-language answers are model-generated and should be checked when accuracy matters.
- English responses are requested through the system prompt, not enforced by a language validator.
- Quantities are supported only in kilograms.
- The calculator uses two-decimal rounding.
- Taxes, discounts, payment processing, authentication, and persistent order records are not implemented.
- The CLI displays a fixed USD notice; keep the sample inventory currency as USD unless you also update that interface.
- Dependency versions are not pinned. For reproducible deployments, record and test specific package versions.

## Educational Purpose

This project demonstrates:

- Local LLM integration with LangChain.
- Graph-based agent orchestration with LangGraph.
- JSON-based action selection.
- Separation of model reasoning from trusted business logic.
- Inventory and basket validation.
- Decimal-based invoice calculation.
- Explicit user authorization for state-changing operations.
- Short-term conversation memory.
