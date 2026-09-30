#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import argparse
import sys
import re
import os

# Import python-dotenv to read the .env file
try:
    from dotenv import load_dotenv
    # Load variables from the .env file
    load_dotenv()
    DOTENV_LOADED = True
except ImportError:
    DOTENV_LOADED = False

# Import NLP Processor
try:
    from nlp_processor import NLPProcessor
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

class AMGRScraper:
    def __init__(self, debug=False):
        self.base_url = "https://www.amgr.org/frm_directorySearch.cfm"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.debug = debug

        # Create the debug folder if it doesn't exist
        if self.debug and not os.path.exists("debug"):
            os.makedirs("debug")

    def get_page_source(self):
        """Fetch the HTML source of the main page"""
        response = self.session.get(self.base_url, headers=self.headers)
        if self.debug:
            with open("debug/main_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Debug - Main page HTML saved to debug/main_page.html")
        return response.content

    def analyze_form_structure(self, html_content=None):
        """Analyze the form structure on the page"""
        if not html_content:
            html_content = self.get_page_source()

        soup = BeautifulSoup(html_content, 'html.parser')

        if self.debug:
            print("Debug - Analyzing form structure...")

            # Check all forms on the page
            forms = soup.find_all('form')
            print(f"Debug - Forms found: {len(forms)}")

            # Check all selects on the page
            selects = soup.find_all('select')
            print(f"Debug - Select elements found: {len(selects)}")
            for i, select in enumerate(selects):
                name = select.get('name')
                id_attr = select.get('id')
                print(f"Debug - Select #{i}: name='{name}', id='{id_attr}'")

            # Check all buttons on the page
            buttons = soup.find_all('button')
            print(f"Debug - Button elements found: {len(buttons)}")
            for i, button in enumerate(buttons):
                text = button.text
                type_attr = button.get('type')
                print(f"Debug - Button #{i}: text='{text}', type='{type_attr}'")

            # Check all inputs on the page
            inputs = soup.find_all('input')
            print(f"Debug - Input elements found: {len(inputs)}")
            for i, input_el in enumerate(inputs):
                name = input_el.get('name')
                type_attr = input_el.get('type')
                print(f"Debug - Input #{i}: name='{name}', type='{type_attr}'")

        # Find form elements by attribute and content
        form_elements = {
            'state_select': None,
            'member_select': None,
            'breed_select': None,
            'submit_input': None
        }

        # Scan all selects
        for select in soup.find_all('select'):
            select_name = select.get('name', '')
            select_id = select.get('id', '')

            if select_name == 'stateID' or 'state' in select_id.lower():
                form_elements['state_select'] = select
                if self.debug:
                    print(f"Debug - Found state select: {select_name}")
            elif select_name == 'memberID' or any(keyword in select_id.lower() for keyword in ['member', 'breeder']):
                form_elements['member_select'] = select
                if self.debug:
                    print(f"Debug - Found member select: {select_name}")
            elif select_name == 'breedID' or 'breed' in select_id.lower():
                form_elements['breed_select'] = select
                if self.debug:
                    print(f"Debug - Found breed select: {select_name}")

        # Find the submit button
        for input_el in soup.find_all('input'):
            if input_el.get('type') == 'submit':
                form_elements['submit_input'] = input_el
                if self.debug:
                    print(f"Debug - Found submit button: input[type='submit']")
                break

        # If not found, look for an input named submitButton
        if not form_elements['submit_input']:
            for input_el in soup.find_all('input'):
                if input_el.get('name') == 'submitButton':
                    form_elements['submit_input'] = input_el
                    if self.debug:
                        print(f"Debug - Found submit button: input[name='submitButton']")
                    break

        # If still not found, look for a button with submit/search text
        if not form_elements['submit_input']:
            for button in soup.find_all('button'):
                button_text = button.text.lower()
                if any(keyword in button_text for keyword in ['submit', 'search', 'find']):
                    form_elements['submit_input'] = button
                    if self.debug:
                        print(f"Debug - Found submit button with text: {button_text}")
                    break

        if self.debug:
            print(f"Debug - Form elements found: state={form_elements['state_select'] is not None}, member={form_elements['member_select'] is not None}, breed={form_elements['breed_select'] is not None}, submit={form_elements['submit_input'] is not None}")

        return form_elements

    def get_options(self):
        """Fetch the available options for state, member, and breed"""
        html_content = self.get_page_source()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Analyze the form structure
        form_elements = self.analyze_form_structure(html_content)

        states = {}
        members = {}
        breeds = {}

        # Collect states
        state_select = form_elements['state_select']
        if state_select:
            for option in state_select.find_all('option')[1:]:  # Skip the first one (-- Select State --)
                option_text = option.text.strip()
                if option_text and not option_text.startswith("-- Select"):
                    states[option_text] = option.get('value')

        # Collect members
        member_select = form_elements['member_select']
        if member_select:
            for option in member_select.find_all('option')[1:]:  # Skip the first one (-- Select Member --)
                option_text = option.text.strip()
                if option_text and not option_text.startswith("-- Select"):
                    members[option_text] = option.get('value')

        # Collect breeds
        breed_select = form_elements['breed_select']
        if breed_select:
            for option in breed_select.find_all('option')[1:]:  # Skip the first one (-- Select Breed --)
                option_text = option.text.strip()
                if option_text and not option_text.startswith("-- Select"):
                    breeds[option_text] = option.get('value')

        if self.debug:
            print(f"Debug - States found: {len(states)}")
            print(f"Debug - Members found: {len(members)}")
            print(f"Debug - Breeds found: {len(breeds)}")

            # Print a few examples
            if states:
                print(f"Debug - Example states: {list(states.items())[:3]}")
            if members:
                print(f"Debug - Example members: {list(members.items())[:3]}")
            if breeds:
                print(f"Debug - Example breeds: {list(breeds.items())[:3]}")

        return {
            'states': states,
            'members': members,
            'breeds': breeds
        }

    def search(self, state=None, member=None, breed=None):
        """Run a search with the given filters"""
        # Check the given parameters
        if not state and not member and not breed:
            if self.debug:
                print("Debug - No search parameters provided")
            return {"header": [], "data": []}

        # Get the available options and form elements
        options = self.get_options()
        form_elements = self.analyze_form_structure()

        # Build the form data
        data = {}

        # Resolve the state value
        if state and options['states']:
            # Try an exact match
            if state in options['states']:
                data['stateID'] = options['states'][state]
                if self.debug:
                    print(f"Debug - Using state value: {state} -> {options['states'][state]}")
            else:
                # Fall back to a substring match
                matched = False
                for state_name, state_value in options['states'].items():
                    if state.lower() in state_name.lower():
                        data['stateID'] = state_value
                        if self.debug:
                            print(f"Debug - Found state by partial match: {state} -> {state_name} ({state_value})")
                        matched = True
                        break

                if not matched and self.debug:
                    print(f"Debug - State '{state}' not found in available options")

        # Resolve the member value
        if member and options['members']:
            # Try an exact match
            if member in options['members']:
                data['memberID'] = options['members'][member]
                if self.debug:
                    print(f"Debug - Using member value: {member} -> {options['members'][member]}")
            else:
                # Fall back to a substring match
                matched = False
                for member_name, member_value in options['members'].items():
                    if member.lower() in member_name.lower():
                        data['memberID'] = member_value
                        if self.debug:
                            print(f"Debug - Found member by partial match: {member} -> {member_name} ({member_value})")
                        matched = True
                        break

                if not matched and self.debug:
                    print(f"Debug - Member '{member}' not found in available options")

        # Resolve the breed value
        if breed and options['breeds']:
            # Try an exact match
            if breed in options['breeds']:
                data['breedID'] = options['breeds'][breed]
                if self.debug:
                    print(f"Debug - Using breed value: {breed} -> {options['breeds'][breed]}")
            else:
                # Fall back to a substring match
                matched = False
                for breed_name, breed_value in options['breeds'].items():
                    if breed.lower() in breed_name.lower():
                        data['breedID'] = breed_value
                        if self.debug:
                            print(f"Debug - Found breed by partial match: {breed} -> {breed_name} ({breed_value})")
                        matched = True
                        break

                if not matched and self.debug:
                    print(f"Debug - Breed '{breed}' not found in available options")

        # If no filter could be added,
        # make sure the form still gets submitted
        if not data:
            data = {'submit': 'Submit'}

        # Add the submit button value if present
        submit_input = form_elements.get('submit_input')
        if submit_input and submit_input.get('name'):
            submit_name = submit_input.get('name')
            submit_value = submit_input.get('value', 'Submit')
            data[submit_name] = submit_value
            if self.debug:
                print(f"Debug - Adding submit button: {submit_name}={submit_value}")

        if self.debug:
            print(f"\nDebug - Data sent: {data}")

        # Send the request
        response = self.session.post(self.base_url, data=data, headers=self.headers)

        if self.debug:
            print(f"Debug - Status code: {response.status_code}")
            print(f"Debug - Response URL: {response.url}")
            with open("debug/response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Debug - Response HTML saved to debug/response.html")

        # Parse the search results
        results = self._parse_results(response.content)
        return results

    def _parse_results(self, html_content):
        """Parse the search results table from the HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all tables on the page
        tables = soup.find_all('table')
        if self.debug:
            print(f"Debug - Tables found: {len(tables)}")

        # Try to find the results table
        result_table = None
        for i, table in enumerate(tables):
            # Check whether this table has relevant data
            table_text = table.get_text()
            if self.debug:
                print(f"Debug - Table #{i} text preview: {table_text[:100]}...")

            # Look for a table with relevant content
            if any(keyword in table_text.lower() for keyword in ['name', 'state', 'phone', 'farm']):
                result_table = table
                if self.debug:
                    print(f"Debug - Found result table #{i}")
                break

        # If none matched, fall back to the first table
        if not result_table and tables:
            result_table = tables[0]
            if self.debug:
                print("Debug - Using first table as result table")

        # No tables at all, return an empty result
        if not result_table:
            if self.debug:
                print("Debug - No result table found")
            return {"header": [], "data": []}

        # Parse header
        headers = []
        header_row = result_table.find('thead')
        if header_row:
            # There's a thead, look for th cells inside it
            header_cells = header_row.find_all('th')
            if header_cells:
                headers = [cell.get_text().strip() for cell in header_cells]

        # No header in thead, try the first row
        if not headers:
            first_row = result_table.find('tr')
            if first_row:
                # Look for th cells in the first row
                header_cells = first_row.find_all('th')
                if header_cells:
                    headers = [cell.get_text().strip() for cell in header_cells]
                    # Skip this row when reading data
                    rows = result_table.find_all('tr')[1:]
                else:
                    # No th cells, the first row's td cells may be the header
                    header_cells = first_row.find_all('td')
                    if header_cells:
                        headers = [cell.get_text().strip() for cell in header_cells]
                        # Skip this row when reading data
                        rows = result_table.find_all('tr')[1:]
            else:
                rows = result_table.find_all('tr')
        else:
            # Header came from thead, so read all rows in tbody
            tbody = result_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # No tbody, take every tr except the first
                rows = result_table.find_all('tr')[1:]

        # Still no header, use the defaults
        if not headers:
            if self.debug:
                print("Debug - Using default headers")
            headers = ["State", "Name", "Farm", "Phone", "Website"]

        # Parse data
        data = []
        for row in rows:
            cells = row.find_all('td')
            if cells:
                row_data = [cell.get_text().strip() for cell in cells]
                # Only add non-empty rows
                if any(cell for cell in row_data):
                    # If the first column is Action and it's empty, fill it with "navigate_pagination"
                    if headers and headers[0] == "Action" and (not row_data[0] or row_data[0] == ""):
                        row_data[0] = "navigate_pagination"
                    data.append(row_data)

        if self.debug:
            print(f"Debug - Headers found: {headers}")
            print(f"Debug - Data rows found: {len(data)}")
            if data:
                print(f"Debug - Sample data row: {data[0]}")

        return {
            "header": headers,
            "data": data
        }

def interactive_mode():
    """Interactive mode for the script"""
    print("=" * 50)
    print("MrScraper - AMGR Directory Scraper [Interactive Mode]")
    print("=" * 50)

    # Enable debug mode
    debug_mode = input("\nEnable debug mode? (y/n, default=n): ").lower().strip() == 'y'

    # Ask whether to use natural language mode
    use_nl = input("\nUse Natural Language mode? (y/n, default=n): ").lower().strip() == 'y'

    scraper = AMGRScraper(debug=debug_mode)

    print(f"\nLink: {scraper.base_url}")

    selected_state = None
    selected_member = None
    selected_breed = None

    if use_nl:
        # Check whether NLP is available
        if not NLP_AVAILABLE:
            print("Error: Natural language feature is unavailable. Make sure nlp_processor.py exists and its dependencies are installed.")
            print("Continuing in regular interactive mode...")
        else:
            try:
                # Get the API key from the environment
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    print("\nError: OPENAI_API_KEY not found in environment variables.")

                    if not DOTENV_LOADED:
                        print("Note: python-dotenv is not installed or failed to load.")
                        print("Install it with: pip install python-dotenv")

                    print("\nTo use the natural language feature, set the environment variable first")
                    print("or create a .env file containing:")
                    print("OPENAI_API_KEY=your-api-key-here")
                    print("\nSetting the environment variable:")
                    print("  Windows: set OPENAI_API_KEY=your-api-key-here")
                    print("  Linux/Mac: export OPENAI_API_KEY=your-api-key-here")
                    print("\nContinuing in regular interactive mode...")
                    use_nl = False

                if use_nl:
                    # Initialize the NLP processor
                    processor = NLPProcessor(api_key=api_key)

                    # Ask for a natural language query
                    nl_query = input("\nEnter your search in natural language: ")
                    if nl_query.strip():
                        print(f"\nAnalyzing query: \"{nl_query}\"")
                        params = processor.parse_command(nl_query)

                        # Use the parsed parameters
                        selected_state = params.get('state')
                        selected_member = params.get('member')
                        selected_breed = params.get('breed')

                        print("\nParsed parameters:")
                        print(f"- State: {selected_state or 'not specified'}")
                        print(f"- Member: {selected_member or 'not specified'}")
                        print(f"- Breed: {selected_breed or 'not specified'}")

                        # Confirm the parsed parameters
                        confirm = input("\nUse these parameters? (y/n, default=y): ").lower().strip()
                        if confirm and confirm != 'y':
                            print("Continuing in regular interactive mode...")
                            use_nl = False
                    else:
                        print("Empty query. Continuing in regular interactive mode...")
                        use_nl = False
            except Exception as e:
                print(f"Error processing natural language query: {e}")
                print("Continuing in regular interactive mode...")
                use_nl = False

    # Without natural language (or after an error), use the regular interactive flow
    if not use_nl:
        # Fetch the available options
        print("\nFetching available options from the site...")
        options = scraper.get_options()

        # State selection
        print("\n--- Select State ---")
        states = list(options['states'].keys())
        for i, state in enumerate(states, 1):
            print(f"{i}. {state}")

        state_choice = input("\nSelect state (number or name, leave blank to skip): ")

        if state_choice.strip():
            # Input is a number
            if state_choice.isdigit():
                idx = int(state_choice) - 1
                if 0 <= idx < len(states):
                    selected_state = states[idx]
                    print(f"Command: Select State: \"{selected_state}\"")
            # Input is a state name
            else:
                selected_state = state_choice
                print(f"Command: Select State: \"{selected_state}\"")

        # Member selection
        print("\n--- Select Member ---")
        members = list(options['members'].keys())
        for i, member in enumerate(members, 1):
            print(f"{i}. {member}")

        member_choice = input("\nSelect member (number or name, leave blank to skip): ")

        if member_choice.strip():
            # Input is a number
            if member_choice.isdigit():
                idx = int(member_choice) - 1
                if 0 <= idx < len(members):
                    selected_member = members[idx]
                    print(f"Command: Select Member: \"{selected_member}\"")
            # Input is a member name
            else:
                selected_member = member_choice
                print(f"Command: Select Member: \"{selected_member}\"")

        # Breed selection
        print("\n--- Select Breed ---")
        breeds = list(options['breeds'].keys())
        for i, breed in enumerate(breeds, 1):
            print(f"{i}. {breed}")

        breed_choice = input("\nSelect breed (number or name, leave blank to skip): ")

        if breed_choice.strip():
            # Input is a number
            if breed_choice.isdigit():
                idx = int(breed_choice) - 1
                if 0 <= idx < len(breeds):
                    selected_breed = breeds[idx]
                    print(f"Command: Select Breed: \"{selected_breed}\"")
            # Input is a breed name
            else:
                selected_breed = breed_choice
                print(f"Command: Select Breed: \"{selected_breed}\"")

    # Run the search
    print("\nSearching...")
    results = scraper.search(selected_state, selected_member, selected_breed)

    # Show the results
    print("\nSearch results:")
    print(json.dumps(results, indent=2))

def main():
    # Check whether any arguments were given
    if len(sys.argv) == 1:
        # No arguments: run interactive mode
        interactive_mode()
        return

    # Otherwise run in command line mode
    parser = argparse.ArgumentParser(description='AMGR Directory Scraper')
    parser.add_argument('--state', type=str, help='State filter')
    parser.add_argument('--member', type=str, help='Member filter')
    parser.add_argument('--breed', type=str, help='Breed filter')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    # Natural Language Processing option
    parser.add_argument('--nl', '--natural-language', type=str, dest='nl_query',
                        help='Search query in natural language')

    args = parser.parse_args()

    # Process the natural language query, if any
    if args.nl_query:
        if not NLP_AVAILABLE:
            print("Error: Natural language feature is unavailable. Make sure nlp_processor.py exists and its dependencies are installed.")
            sys.exit(1)

        try:
            # Get the API key from the environment
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("Error: OPENAI_API_KEY not found in environment variables.")

                if not DOTENV_LOADED:
                    print("Note: python-dotenv is not installed or failed to load.")
                    print("Install it with: pip install python-dotenv")

                print("\nTo use the natural language feature, set the environment variable first")
                print("or create a .env file containing:")
                print("OPENAI_API_KEY=your-api-key-here")
                print("\nSetting the environment variable:")
                print("  Windows: set OPENAI_API_KEY=your-api-key-here")
                print("  Linux/Mac: export OPENAI_API_KEY=your-api-key-here")
                sys.exit(1)

            # Initialize the NLP Processor
            processor = NLPProcessor(api_key=api_key)

            print(f"Analyzing query: \"{args.nl_query}\"")
            params = processor.parse_command(args.nl_query)

            # Use the parameters parsed by NLP
            args.state = params.get('state')
            args.member = params.get('member')
            args.breed = params.get('breed')

            print("Parsed parameters:")
            print(f"- State: {args.state or 'not specified'}")
            print(f"- Member: {args.member or 'not specified'}")
            print(f"- Breed: {args.breed or 'not specified'}")
            print()

        except Exception as e:
            print(f"Error processing natural language query: {e}")
            print("Continuing with the directly provided parameters (if any).")

    scraper = AMGRScraper(debug=args.debug)

    print("Insert Link:", scraper.base_url)

    if args.state:
        print(f"Command: Select State: \"{args.state}\"")
    if args.member:
        print(f"Command: Select Member: \"{args.member}\"")
    if args.breed:
        print(f"Command: Select Breed: \"{args.breed}\"")

    results = scraper.search(args.state, args.member, args.breed)

    # Print the results as JSON
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
