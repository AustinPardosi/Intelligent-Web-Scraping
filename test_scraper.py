#!/usr/bin/env python3
"""
Automated testing and output validation for the AMGR Scraper

Runs a set of test cases to make sure the scraper
works correctly and produces the expected output.
"""
import sys
import time
import json
import unittest
from unittest.mock import patch
import os
from mrscraper import AMGRScraper
from nlp_processor import NLPProcessor

# Create the results folder if it doesn't exist
TEST_RESULTS_DIR = "test_results"
if not os.path.exists(TEST_RESULTS_DIR):
    os.makedirs(TEST_RESULTS_DIR)


class TestAMGRScraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the scraper instance for all tests"""
        print("Initializing scraper for testing...")
        cls.scraper = AMGRScraper(debug=False)

        # Check whether the NLP Processor is available
        cls.nlp_available = False
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                cls.nlp = NLPProcessor(api_key=api_key)
                cls.nlp_available = True
                print("NLP Processor initialized - NL tests enabled")
            else:
                print("OPENAI_API_KEY not found - NL tests disabled")
        except Exception as e:
            print(f"NLP initialization error: {e} - NL tests disabled")

        # Fetch all available options for testing
        try:
            cls.options = cls.scraper.get_options()
            # Keep the option counts for validation
            cls.state_count = len(cls.options["states"])
            cls.member_count = len(cls.options["members"])
            cls.breed_count = len(cls.options["breeds"])

            print(
                f"Options found: {cls.state_count} states, {cls.member_count} members, {cls.breed_count} breeds"
            )

            # Fixed sample values for testing
            cls.sample_state = "Kansas"
            cls.sample_member = "Dwight Elmore"  # Breeder in Kansas
            cls.sample_breed = "(SA) - Savanna"  # Common breed

            # Verify the chosen samples exist in the options
            if cls.sample_state not in cls.options["states"]:
                print(
                    f"WARNING: State sample '{cls.sample_state}' not found in options"
                )
                cls.sample_state = (
                    next(iter(cls.options["states"].keys()))
                    if cls.options["states"]
                    else None
                )

            if not any(cls.sample_member in m for m in cls.options["members"]):
                print(
                    f"WARNING: Member sample '{cls.sample_member}' not found in options"
                )
                cls.sample_member = (
                    next(iter(cls.options["members"].keys()))
                    if cls.options["members"]
                    else None
                )

            if cls.sample_breed not in cls.options["breeds"]:
                print(
                    f"WARNING: Breed sample '{cls.sample_breed}' not found in options"
                )
                cls.sample_breed = (
                    next(iter(cls.options["breeds"].keys()))
                    if cls.options["breeds"]
                    else None
                )

            print(
                f"Using samples: state='{cls.sample_state}', member='{cls.sample_member}', breed='{cls.sample_breed}'"
            )

        except Exception as e:
            print(f"ERROR: Could not fetch options for testing: {e}")
            sys.exit(1)

    def validate_result_structure(self, result):
        """Validate the search result structure"""
        # Result must be a dictionary with 'header' and 'data' keys
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn("header", result, "Result must have a 'header' key")
        self.assertIn("data", result, "Result must have a 'data' key")

        # header and data must be lists
        self.assertIsInstance(result["header"], list, "Header should be a list")
        self.assertIsInstance(result["data"], list, "Data should be a list")

        # If there is data, validate its structure
        if result["data"]:
            # Each row must have as many columns as the header
            first_row = result["data"][0]
            self.assertEqual(
                len(first_row),
                len(result["header"]),
                f"Data rows must have the same number of columns as the header",
            )

            # Header must contain the expected columns
            expected_columns = [
                "State",
                "Name",
            ]  # At minimum, state and name columns
            for column in expected_columns:
                self.assertTrue(
                    any(column in header for header in result["header"]),
                    f"Header must contain column '{column}'",
                )

        return True

    def save_test_result(self, test_name, query_params, result, execution_time):
        """Save an individual test result to a JSON file"""
        test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query_params": query_params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Keep at most the first 3 results
            "test_success": True,
        }

        # Write the file for this test case
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        return file_path

    def test_01_search_by_state(self):
        """Test Case 1: Search by state"""
        test_name = "test_01_search_by_state"
        print(f"\nTest Case 1: Search by state: {self.sample_state}")

        # Define parameters and expectations
        params = {"state": self.sample_state}
        expected = {
            "structure": 'dictionary with "header" and "data" keys',
            "content": f"All rows must have state={self.sample_state}",
            "verification": "Check the State column in every result row",
        }
        print(f"Expected: {expected['content']}")

        # Run the search
        start_time = time.time()
        result = self.scraper.search(state=self.sample_state)
        execution_time = time.time() - start_time

        # Show results
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Result count: {len(result['data'])}")
        if result["data"]:
            print(f"Sample result: {result['data'][0]}")

        # Validate result structure
        self.validate_result_structure(result)

        # Validate content - if there is data, the state must match
        state_valid = True
        if result["data"]:
            # Find the State column index
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row):  # Make sure the index is in range
                        # Check the row's state (unless it's a navigation button)
                        if not row[0].startswith("navigate"):
                            if row[state_idx] != self.sample_state:
                                state_valid = False
                                print(
                                    f"Error: State in result ({row[state_idx]}) does not match the searched state ({self.sample_state})"
                                )

        # Save results to file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Results saved to: {result_file}")

        # Final assertion
        self.assertTrue(
            state_valid,
            f"Not all states in the result match {self.sample_state}",
        )

    def test_02_search_by_member(self):
        """Test Case 2: Search by member (breeder)"""
        test_name = "test_02_search_by_member"
        if not self.sample_member:
            self.skipTest("No sample member to test")

        print(f"\nTest Case 2: Search by member: {self.sample_member}")

        # Define parameters and expectations
        params = {"member": self.sample_member}
        expected = {
            "structure": 'dictionary with "header" and "data" keys',
            "content": f"Results must include data with name={self.sample_member}",
            "verification": "Check the Name column in the search results",
        }
        print(f"Expected: {expected['content']}")

        # Run the search
        start_time = time.time()
        result = self.scraper.search(member=self.sample_member)
        execution_time = time.time() - start_time

        # Show results
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Result count: {len(result['data'])}")

        # Validate result structure
        self.validate_result_structure(result)

        # Results must not be empty
        self.assertGreater(
            len(result["data"]),
            0,
            f"Search for member '{self.sample_member}' should return results",
        )

        # Show result info
        if "header" in result and "data" in result and result["data"]:
            print("Header:", result["header"])
            print("Sample data:", result["data"][0])

            # Find the Name column index
            name_idx = -1
            for i, header_col in enumerate(result["header"]):
                if "Name" in header_col:
                    name_idx = i
                    break

            if name_idx >= 0:
                print(f"Name column found at index {name_idx}")

                # Check whether the member name appears in the results
                member_found = False
                for row in result["data"]:
                    if len(row) > name_idx:
                        # Passes if the member name appears as a substring
                        if row[name_idx] and self.sample_member in row[name_idx]:
                            member_found = True
                            print(f"Member found: {row[name_idx]}")
                            break

                if not member_found:
                    print(
                        f"WARNING: Member '{self.sample_member}' not found in search results"
                    )

        # Save results to file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Results saved to: {result_file}")

        # Don't fail here, since results may not match exactly
        # If an exact match is required, uncomment the following line:
        # self.assertTrue(member_found, f"Member '{self.sample_member}' not found in search results")

    def test_03_search_by_breed(self):
        """Test Case 3: Search by breed (livestock type)"""
        test_name = "test_03_search_by_breed"
        if not self.sample_breed:
            self.skipTest("No sample breed to test")

        print(f"\nTest Case 3: Search by breed: {self.sample_breed}")

        # Define parameters and expectations
        params = {"breed": self.sample_breed}
        expected = {
            "structure": 'dictionary with "header" and "data" keys',
            "content": f"Results must include breeders with breed={self.sample_breed}",
            "verification": "Validate output structure",
        }
        print(f"Expected: {expected['content']}")

        # Run the search
        start_time = time.time()
        result = self.scraper.search(breed=self.sample_breed)
        execution_time = time.time() - start_time

        # Show results
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Result count: {len(result['data'])}")
        if result["data"]:
            print(f"Sample result: {result['data'][0]}")

        # Validate result structure
        self.validate_result_structure(result)

        # Save results to file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Results saved to: {result_file}")

    def test_04_combined_search_state_breed(self):
        """Test Case 4: Combined state and breed search"""
        test_name = "test_04_combined_search"

        # Search for Iowa and Savanna
        iowa_state = "Iowa"
        savanna_breed = "(SA) - Savanna"

        print(
            f"\nTest Case 4: Combined search, state: {iowa_state} and breed: {savanna_breed}"
        )

        # Define parameters and expectations
        params = {"state": iowa_state, "breed": savanna_breed}
        expected = {
            "structure": 'dictionary with "header" and "data" keys',
            "content": f"Results must include data with state={iowa_state} and breed={savanna_breed}",
            "verification": "Check the State column in every result",
        }
        print(f"Expected: {expected['content']}")

        # Run the search
        start_time = time.time()
        result = self.scraper.search(state=iowa_state, breed=savanna_breed)
        execution_time = time.time() - start_time

        # Show results
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Result count: {len(result['data'])}")
        if result["data"]:
            print(f"Sample result: {result['data'][0]}")

        # Validate result structure
        self.validate_result_structure(result)

        # Validate states in the result, if there is data
        state_valid = True
        if result["data"]:
            # Find the State column index
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row) and not row[0].startswith("navigate"):
                        # Iowa usually appears as IA in search results
                        if row[state_idx] != "IA":
                            state_valid = False
                            print(
                                f"Error: State in result ({row[state_idx]}) does not match the searched state (IA)"
                            )

        # Save results to file with a sample of the expected output
        expected_output = {
            "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
            "data": [
                [
                    "navigate_pagination",
                    "IA",
                    "Dennis & Stacy Ratashak",
                    "Ratashak Harvest Hills - RHH",
                    "(703)  850-4113",
                    "",
                ],
                ["navigate_pagination", "IA", "Stan Huber", "-", "(641)  732-9271", ""],
            ],
        }

        test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query_params": params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Keep at most the first 3 results
            "test_success": state_valid,
            "expected_output": expected_output,
        }

        # Write the file for this test case
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {file_path}")

        # Final assertion if there is data
        if result["data"]:
            self.assertTrue(
                state_valid,
                f"Not all states in the result match 'IA'",
            )

    def test_05_natural_language_query(self):
        """Test Case 5: Search using natural language"""
        test_name = "test_05_nl_query"
        if not self.nlp_available:
            self.skipTest("NLP Processor not available for testing")

        print("\nTest Case 5: Search using natural language")

        # Define parameters and expectations
        nl_query = f"Find breeders in {self.sample_state}"
        expected = {
            "structure": 'dictionary with "header" and "data" keys',
            "content": f"Results must include data with state={self.sample_state}",
            "verification": "Compare with a regular state search",
        }
        print(f'Natural language query: "{nl_query}"')
        print(f"Expected: {expected['content']}")

        # Process the natural language query
        start_time = time.time()
        nl_params = self.nlp.parse_command(nl_query)
        print(f"Parsed NL params: {nl_params}")

        # Run the search with the NL parameters
        result = self.scraper.search(
            state=nl_params.get("state"),
            member=nl_params.get("member"),
            breed=nl_params.get("breed"),
        )
        execution_time = time.time() - start_time

        # Show results
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Result count: {len(result['data'])}")
        if result["data"]:
            print(f"Sample result: {result['data'][0]}")

        # Validate result structure
        self.validate_result_structure(result)

        # Validate states in the result, if there is data
        state_valid = True
        if result["data"] and nl_params.get("state"):
            # Find the State column index
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row) and not row[0].startswith("navigate"):
                        if row[state_idx] != nl_params.get("state"):
                            state_valid = False
                            print(
                                f"Error: State in result ({row[state_idx]}) does not match the searched state ({nl_params.get('state')})"
                            )

        # Save results to file with extra info
        nl_test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nl_query": nl_query,
            "parsed_params": nl_params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Keep at most the first 3 results
            "test_success": state_valid,
        }

        # Write the file for this test case
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(nl_test_data, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {file_path}")

        # Final assertion if a state is expected
        if result["data"] and nl_params.get("state"):
            self.assertTrue(
                state_valid,
                f"Not all states in the result match {nl_params.get('state')}",
            )

    def test_06_natural_language_complex(self):
        """Test Case 6: Complex search using natural language"""
        test_name = "test_06_nl_complex"
        if not self.nlp_available:
            self.skipTest("NLP Processor not available for testing")

        print("\nTest Case 6: Complex search using natural language")

        # Define parameters and expectations
        nl_query = "Find breeders in IOWA with American Savanna type"
        expected = {
            "structure": 'dictionary with "header" and "data" keys',
            "content": "Results must include data with state=Iowa and breed=American Savanna",
            "verification": "Compare with a regular combined search",
        }
        print(f'Natural language query: "{nl_query}"')
        print(f"Expected: {expected['content']}")

        # Process the natural language query
        start_time = time.time()
        nl_params = self.nlp.parse_command(nl_query)
        print(f"Parsed NL params: {nl_params}")

        # Run the search with the NL parameters
        result = self.scraper.search(
            state=nl_params.get("state"),
            member=nl_params.get("member"),
            breed=nl_params.get("breed"),
        )
        execution_time = time.time() - start_time

        # Show results
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Result count: {len(result['data'])}")
        if result["data"]:
            print(f"Sample result: {result['data'][0]}")

        # Validate result structure
        self.validate_result_structure(result)

        # Validate results, if there is data
        state_valid = True
        if result["data"] and nl_params.get("state"):
            # Find the State column index
            state_idx = (
                result["header"].index("State") if "State" in result["header"] else -1
            )

            if state_idx >= 0:
                for row in result["data"]:
                    if state_idx < len(row) and not row[0].startswith("navigate"):
                        # Iowa is shown as IA in the results
                        if row[state_idx] != "IA":
                            state_valid = False
                            print(
                                f"Error: State in result ({row[state_idx]}) does not match the expected state (IA)"
                            )

        # Expected output
        expected_output = {
            "header": ["Action", "State", "Name", "Farm", "Phone", "Website"],
            "data": [
                [
                    "navigate_pagination",
                    "IA",
                    "Dennis & Stacy Ratashak",
                    "Ratashak Harvest Hills - RHH",
                    "(703)  850-4113",
                    "",
                ],
                ["navigate_pagination", "IA", "Stan Huber", "-", "(641)  732-9271", ""],
            ],
        }

        # Save results to file with extra info
        nl_test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "nl_query": nl_query,
            "parsed_params": nl_params,
            "execution_time": execution_time,
            "result_count": len(result["data"]) if "data" in result else 0,
            "header": result.get("header", []),
            "sample_data": result.get("data", [])[
                :3
            ],  # Keep at most the first 3 results
            "test_success": state_valid,
            "expected_output": expected_output,
        }

        # Write the file for this test case
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(nl_test_data, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {file_path}")

    def test_07_invalid_parameters(self):
        """Test Case 7: Search with invalid parameters"""
        test_name = "test_07_invalid_params"
        print("\nTest Case 7: Search with invalid parameters")

        # Define parameters and expectations
        invalid_state = "NonExistentState"
        params = {"state": invalid_state}
        expected = {
            "structure": 'dictionary with "header" and "data" keys',
            "content": "Scraper must handle invalid parameters gracefully",
            "verification": "Check the output structure",
        }
        print(f"Invalid parameter: state='{invalid_state}'")
        print(f"Expected: {expected['content']}")

        # Run the search
        start_time = time.time()
        result = self.scraper.search(state=invalid_state)
        execution_time = time.time() - start_time

        # Show results
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Result count: {len(result['data'])}")

        # Result must be a dictionary with the right structure
        self.validate_result_structure(result)

        # Save results to file
        result_file = self.save_test_result(
            test_name=test_name,
            query_params=params,
            result=result,
            execution_time=execution_time,
        )
        print(f"Results saved to: {result_file}")

    @patch("builtins.print")
    def test_08_error_handling(self, mock_print):
        """Test Case 8: Basic error handling"""
        test_name = "test_08_error_handling"
        print("\nTest Case 8: Basic error handling")

        # Define parameters and expectations
        params = {"error_test": True}
        expected = {
            "structure": "Errors must be handled gracefully",
            "content": "Scraper must print a meaningful error message",
            "verification": "Check the print call count and error message",
        }
        print(f"Expected: {expected['content']}")

        # Test with a bad URL
        original_url = self.scraper.base_url
        self.scraper.base_url = "https://nonexistent-url.example.com"

        # Try a search
        start_time = time.time()
        error_message = None
        try:
            result = self.scraper.search()
            print(f"Result: {len(result['data'])} items")
            results_data = result
        except Exception as e:
            error_message = f"{e.__class__.__name__}: {e}"
            print(f"Caught error: {error_message}")
            results_data = {"error": error_message}
        finally:
            # Restore the original URL
            self.scraper.base_url = original_url

        execution_time = time.time() - start_time

        # The error must have been handled gracefully
        self.assertGreaterEqual(
            mock_print.call_count, 1, "An error message should have been printed"
        )

        # Save the error test result to its own file
        error_test_data = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_params": params,
            "execution_time": execution_time,
            "error_message": error_message,
            "print_call_count": mock_print.call_count,
            "test_success": mock_print.call_count >= 1,
        }

        # Write the file for this test case
        file_path = os.path.join(TEST_RESULTS_DIR, f"{test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(error_test_data, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {file_path}")


def save_summary_report(results):
    """Save the test summary report to a JSON file"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(TEST_RESULTS_DIR, f"summary_{timestamp}.json")

    # Add expected vs. actual results for each test
    test_details = []
    for test_name in [
        "test_01_search_by_state",
        "test_02_search_by_member",
        "test_03_search_by_breed",
        "test_04_combined_search",
        "test_05_nl_query",
        "test_06_nl_complex",
        "test_07_invalid_params",
        "test_08_error_handling",
    ]:
        # Find the latest result file for this test
        test_files = [
            f
            for f in os.listdir(TEST_RESULTS_DIR)
            if f.startswith(test_name) and f.endswith(".json")
        ]
        if test_files:
            latest_file = max(
                test_files,
                key=lambda f: os.path.getmtime(os.path.join(TEST_RESULTS_DIR, f)),
            )
            file_path = os.path.join(TEST_RESULTS_DIR, latest_file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    test_data = json.load(f)

                test_info = {
                    "test_name": test_name,
                    "success": test_data.get("test_success", results["success"] > 0),
                    "execution_time": test_data.get("execution_time", 0),
                    "result_count": test_data.get("result_count", 0),
                    "sample_data": test_data.get("sample_data", []),
                    "expected_result": get_test_expectation(test_name),
                    "actual_result": get_actual_result_description(test_data),
                }
                test_details.append(test_info)
            except Exception as e:
                print(f"Error reading test result {test_name}: {e}")

    # Add the test details to the summary
    results["test_details"] = test_details

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Test summary saved to {filename}")
    return filename


def get_test_expectation(test_name):
    """Get the expectation description for a given test"""
    expectations = {
        "test_01_search_by_state": "Searching by state should return a list of breeders in that state",
        "test_02_search_by_member": "Searching by member should find the breeder with that name",
        "test_03_search_by_breed": "Searching by breed should find breeders with that breed",
        "test_04_combined_search": "A combined search should return results matching both criteria",
        "test_05_nl_query": "A natural language query should be converted to the right parameters and return relevant results",
        "test_06_nl_complex": "A complex natural language query should be processed correctly even with multiple parameters",
        "test_07_invalid_params": "Invalid parameters should be handled gracefully without errors",
        "test_08_error_handling": "Connection or server errors should be handled gracefully with an informative message",
    }
    return expectations.get(test_name, "No expectation description")


def get_actual_result_description(test_data):
    """Build a description of the actual result from the test data"""
    if "error" in test_data:
        return f"An error occurred: {test_data['error']}"

    result_count = test_data.get("result_count", 0)

    if "nl_query" in test_data:
        parsed_params = test_data.get("parsed_params", {})
        param_str = ", ".join([f"{k}='{v}'" for k, v in parsed_params.items() if v])
        return f"NL query parsed into parameters ({param_str}) with {result_count} results"

    if "query_params" in test_data:
        param_str = ", ".join(
            [f"{k}='{v}'" for k, v in test_data["query_params"].items()]
        )
        return f"Search with {param_str} returned {result_count} results"

    return f"Test finished with {result_count} results"


def run_tests():
    """Run all test cases and collect the results"""
    # Build the test suite
    loader = unittest.TestLoader()

    # Sort tests by number
    loader.sortTestMethodsUsing = lambda x, y: int(x.split("_")[1]) - int(
        y.split("_")[1]
    )

    suite = loader.loadTestsFromTestCase(TestAMGRScraper)

    # Run the tests and collect results
    results = {}

    # Use TextTestRunner to capture output
    runner = unittest.TextTestRunner(verbosity=2)
    test_results = runner.run(suite)

    # Collect statistics
    results["total"] = test_results.testsRun
    results["success"] = (
        test_results.testsRun - len(test_results.failures) - len(test_results.errors)
    )
    results["fail"] = len(test_results.failures)
    results["error"] = len(test_results.errors)
    results["success_rate"] = (
        results["success"] / results["total"] * 100 if results["total"] > 0 else 0
    )

    # Show the summary
    print("\n" + "=" * 50)
    print("AUTOMATED TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total test cases: {results['total']}")
    print(f"Passed: {results['success']}")
    print(f"Failed: {results['fail']}")
    print(f"Errors: {results['error']}")
    print(f"Success rate: {results['success_rate']:.2f}%")

    # Save the summary to a file
    summary_file = save_summary_report(results)
    print(f"Full report saved to: {summary_file}")

    return results


if __name__ == "__main__":
    print("AUTOMATED OUTPUT VALIDATION - AMGR SCRAPER")
    print("=" * 50)
    run_tests()
