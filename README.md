# MrScraper - AMGR Directory Scraper

A simple Python script for web scraping the [AMGR Directory](https://www.amgr.org/frm_directorySearch.cfm) website.

## Description

This script allows you to search for breeder information in the AMGR Directory using filters such as state, member, and breed type. Results are displayed in JSON format.

## Requirements

-   Python 3.6+
-   Python modules:
    -   requests
    -   beautifulsoup4
    -   requests (for Natural Language feature)

## Installation

1. Make sure Python is installed on your system
2. Install the required modules:

```bash
pip install -r requirements.txt

# For Natural Language feature (optional)
pip install openai
```

## Setting up OpenAI API Key

If you want to use the Natural Language feature, you need to set up the OpenAI API key using one of the following methods:

### 1. Using .env file (Recommended)

Create a file named `.env` in the same directory as the script, then add:

```
OPENAI_API_KEY=your-api-key-here
```

Make sure you have installed python-dotenv:

```
pip install python-dotenv
```

### 2. Using Environment Variable

#### On Windows:

```
set OPENAI_API_KEY=your-api-key-here
```

#### On Linux/Mac:

```
export OPENAI_API_KEY=your-api-key-here
```

The Natural Language feature will not work if the API key is not available through one of the methods above.

## Usage

### Interactive Mode

To use interactive mode (easier for beginners), run the script without arguments:

```bash
python mrscraper.py
```

In this mode, the script will:

1. Ask if you want to enable debug mode
2. Ask if you want to use Natural Language
    - If yes, you can enter commands in natural language
    - The script will analyze your command and translate it to search parameters
3. If not using Natural Language, the script will:
    - Ask you to select a state from the list
    - Ask you to select a member from the list
    - Ask you to select a breed from the list
4. Perform the search and display the results

### Command Line Mode

For more experienced users, the script can be run with parameters:

```bash
python mrscraper.py [OPTIONS]
```

#### Available options:

-   `--state`: Filter by state (e.g., "Kansas")
-   `--member`: Filter by member (e.g., "Dwight Elmore")
-   `--breed`: Filter by breed (e.g., "(AR) - American Red")
-   `--debug`: Enable debug mode (saves HTML files in debug folder)

#### Example:

```bash
python mrscraper.py --state "Kansas" --member "Dwight Elmore"
```

### Natural Language Mode (NEW!)

You can also use natural language commands to perform searches:

```bash
python mrscraper.py --nl "Find breeders named Elmore in Kansas"
```

To use this feature, you need to:

1. Provide OpenAI API key:
    - Via parameter: `--api-key "your-api-key-here"`
    - Or via environment variable: `OPENAI_API_KEY`
    - Or enter interactively when prompted

#### Example natural language commands:

-   "Find breeders in Kansas"
-   "Show all breeders with American Red breed"
-   "Who is the breeder named Dwight Elmore?"
-   "Find breeders in Alabama who have American Black"

## Output

Output is displayed in JSON format with the following structure:

```json
{
    "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
    "data": [
        [
            "navigate_pagination",
            "KS",
            "Dwight Elmore",
            "3TAC Ranch Genetics - 3TR",
            "(620) 899-0770",
            ""
        ],
        [
            "navigate_pagination",
            "KS",
            "Mary Powell",
            "Barnyard Weed Warriors - BWW",
            "(785) 420-0472",
            ""
        ]
    ]
}
```

## Debug Mode

If you encounter problems, enable debug mode:

```bash
python mrscraper.py --debug
```

Debug files will be saved in the `debug/` folder:

-   `main_page.html`: Main page HTML
-   `response.html`: Search results HTML

## Technical Notes

-   The script uses correct field names for form submission: `stateID`, `memberID`, and `breedID`
-   The script has flexible form element detection mechanisms to handle page structure changes
-   Natural Language feature uses OpenAI's `gpt-4o-mini` model

## Automated Output Validation

The `test_scraper.py` script provides automated testing to verify scraper accuracy. This feature allows you to ensure that the scraper works correctly and produces expected output.

### How to Run Tests

```bash
python test_scraper.py
```

### Available Test Cases

The test script includes 8 different test cases:

1. **Search by state** - Tests search capability by state (Kansas)
2. **Search by member** - Tests search capability by breeder name (Dwight Elmore)
3. **Search by breed** - Tests search capability by livestock type
4. **Combined parameter search** - Tests search capability with combination of state and breed (Iowa and Savanna)
5. **Natural Language search** - Tests ability to convert natural language queries to search parameters
6. **Complex NL search** - Tests ability to convert complex queries like "Find breeders in IOWA with American Savanna type"
7. **Invalid parameter search** - Tests resilience against invalid parameters
8. **Error handling** - Tests error handling when connection problems occur

### Test Results

Test results are saved in the `test_results/` folder:

-   Individual files for each test case (e.g., `test_01_search_by_state.json`)
-   Summary file with overall statistics (`summary_TIMESTAMP.json`)

Each test result file contains:

-   Search parameters used
-   Execution time
-   Sample result data
-   Expectations vs actual results

Example test output:

```json
{
    "test_name": "test_04_combined_search",
    "timestamp": "2025-05-17 05:07:32",
    "query_params": {
        "state": "Iowa",
        "breed": "(SA) - Savanna"
    },
    "execution_time": 0.87,
    "result_count": 6,
    "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
    "sample_data": [
        [
            "navigate_pagination",
            "IA",
            "Steve & Syrie Vicary",
            "Vicary Savanna Goats - VSG",
            "(402) 203-2165",
            ""
        ]
    ],
    "test_success": true,
    "expected_output": {
        "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
        "data": [
            [
                "navigate_pagination",
                "IA",
                "Dennis & Stacy Ratashak",
                "Ratashak Harvest Hills - RHH",
                "(703) 850-4113",
                ""
            ]
        ]
    }
}
```

## Notes

-   This script is designed for educational purposes only
-   Use wisely and respect the policies of the accessed website
-   Using the Natural Language feature requires a valid OpenAI API key
