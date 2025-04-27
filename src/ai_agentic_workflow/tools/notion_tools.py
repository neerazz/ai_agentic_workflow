import logging
from typing import List, Dict, Optional, Any

from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

from src.ai_agentic_workflow.utils.env_reader import get_env_variable

logger = logging.getLogger(__name__)


class NotionHelper:
    """
    Helper class to interact with the Notion API for querying databases
    and retrieving page content.

    Handles initialization with API key (from arg or environment variable)
    and provides methods for common Notion tasks.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the Notion Client.

        Args:
            api_key: Notion API Key (integration secret). If None, attempts
                     to read from the "NOTION_API_KEY" environment variable.

        Raises:
            ValueError: If no API key is provided or found in environment variables.
            # NotionClient itself might raise errors on invalid token, though often lazy
        """
        token = api_key or get_env_variable("NOTION_API_KEY")
        if not token:
            logger.error("Notion API Key not provided and not found in environment variable 'NOTION_API_KEY'.")
            raise ValueError("Missing Notion API Key.")

        try:
            self.client = NotionClient(auth=token)
            # Optionally add a check here, e.g., list users, to validate the key early
            # self.client.users.list() # Example check - uncomment if needed
            logger.info("Notion Client initialized successfully.")
        except Exception as e:  # Catch potential errors during NotionClient init
            logger.error(f"Failed to initialize Notion Client: {e}", exc_info=True)
            # Depending on severity, re-raise or handle appropriately
            raise ConnectionError(f"Failed to initialize Notion Client: {e}") from e

    def query_database(
            self,
            database_id: str,
            filter_params: Optional[Dict[str, Any]] = None,
            sorts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries a Notion database with optional filters and sorts.

        Args:
            database_id: The ID of the Notion database to query.
            filter_params: Notion API filter dictionary. See Notion API docs.
            sorts: Notion API sorts list. See Notion API docs.

        Returns:
            A list of Notion page objects (as dictionaries) matching the query,
            or an empty list if no results or an error occurs.
        """
        if not database_id:
            logger.error("Database ID is required for querying.")
            return []

        query: Dict[str, Any] = {"database_id": database_id}
        if filter_params:
            query["filter"] = filter_params
        if sorts:
            query["sorts"] = sorts

        logger.debug(f"Querying Notion database '{database_id}' with params: {query}")
        try:
            response = self.client.databases.query(**query)
            results = response.get("results", [])
            logger.info(f"Found {len(results)} pages in database '{database_id}' matching query.")
            return results
        except APIResponseError as e:
            logger.error(f"Notion API error querying database '{database_id}': {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying database '{database_id}': {e}", exc_info=True)
            return []

    def get_plain_text_for_pages(self, page_ids: List[str]) -> Dict[str, Optional[str]]:
        """
        Retrieves plain text content for multiple page IDs.

        Args:
            page_ids: A list of Notion page IDs.

        Returns:
            A dictionary where keys are the input page IDs and values are the
            extracted plain text (string). If an error occurred fetching content
            for a specific page ID, its value will be None. If a page had no
            extractable text, its value will be an empty string "".
        """
        results: Dict[str, Optional[str]] = {}
        if not page_ids:
            logger.warning("get_plain_text_for_pages called with an empty list of page IDs.")
            return results

        for page_id in page_ids:
            logger.debug(f"Processing request for page content: {page_id}")
            # Call the single-page function which uses the internal helpers
            content = self.get_page_plain_text(page_id)
            results[page_id] = content  # Store content (str) or None

        logger.info(f"Processed content requests for {len(page_ids)} page IDs.")
        return results

    def get_page_plain_text(self, page_id: str) -> Optional[str]:
        """
        Retrieves and concatenates plain text from supported block types
        (paragraphs, headings, bulleted lists) within a Notion page.

        Args:
            page_id: The ID of the Notion page.

        Returns:
            A string containing the concatenated text, or None if an error occurs
            or the page has no supported text blocks.
        """
        if not page_id:
            logger.error("Page ID is required for fetching content.")
            return None

        logger.debug(f"Fetching blocks for page '{page_id}'")
        try:
            # TODO: Implement pagination for pages with > 100 blocks if needed
            response = self.client.blocks.children.list(block_id=page_id)
            blocks = response.get("results", [])
        except APIResponseError as e:
            logger.error(f"Notion API error fetching blocks for page '{page_id}': {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching blocks for page '{page_id}': {e}", exc_info=True)
            return None

        texts: List[str] = []
        for block in blocks:
            block_type = block.get("type")
            block_id = block.get("id", "unknown_id")  # For logging

            try:
                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                    # Extract text from simple rich text blocks
                    rich_text = block.get(block_type, {}).get("rich_text", [])
                    for rt in rich_text:
                        texts.append(rt.get("plain_text", ""))
                    texts.append("\n")  # Add newline after these blocks for structure

                elif block_type == "bulleted_list_item":
                    rich_text = block.get(block_type, {}).get("rich_text", [])
                    item_text = "".join([rt.get("plain_text", "") for rt in rich_text])
                    texts.append(f"* {item_text}")  # Prepend bullet point marker

                # Add elif for other block types (numbered_list_item, todo, code, etc.) if needed
                # Example:
                # elif block_type == "numbered_list_item":
                #     rich_text = block.get(block_type, {}).get("rich_text", [])
                #     item_text = "".join([rt.get("plain_text", "") for rt in rich_text])
                #     # Note: Getting the correct number requires tracking state or more complex logic
                #     texts.append(f"1. {item_text}") # Placeholder number

            except Exception as block_e:
                logger.warning(
                    f"Could not parse block ID '{block_id}' of type '{block_type}' on page '{page_id}': {block_e}",
                    exc_info=False)
                continue  # Skip faulty block

        if not texts:
            logger.info(f"No supported text content found on page '{page_id}'.")
            return ""  # Return empty string instead of None if page exists but has no text

        # Join paragraphs/elements, strip leading/trailing whitespace from the whole result
        return "\n".join(texts).strip()

    def get_excerpts_by_filter(
            self,
            database_id: str,
            filter_params: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Fetches pages based on a provided Notion filter dictionary and
        concatenates their plain text content.

        Args:
            database_id: The ID of the Notion database.
            filter_params: A Notion API filter dictionary. If None, queries all pages
                           (may be inefficient for large databases).

        Returns:
            A single string with concatenated text from matching pages, separated
            by '---'. Returns an empty string "" if no pages match or matching pages
            have no text. Returns None if the initial database query fails (though
            query_database aims to return [] on error).
        """
        log_filter = filter_params if filter_params else "No filter (all pages)"
        logger.info(f"Fetching excerpts for filter '{log_filter}' in database '{database_id}'")

        # 1. Query database using the provided filter
        pages = self.query_database(database_id, filter_params=filter_params)

        # Handle case where query fails or returns no results
        if not pages:
            logger.info(f"No pages found matching the filter in database '{database_id}'.")
            return ""

        # 2. Extract page IDs
        page_ids_to_fetch = [page.get("id") for page in pages if page.get("id")]
        if not page_ids_to_fetch:
            logger.warning(f"Found {len(pages)} page objects from filter, but couldn't extract valid page IDs.")
            return ""

        # 3. Fetch content for these specific IDs
        content_map = self.get_plain_text_for_pages(page_ids_to_fetch)

        # 4. Collect and combine non-empty, non-None results
        excerpts: List[str] = []
        successful_fetches = 0
        for page_id in page_ids_to_fetch:  # Iterate in order of original query
            content = content_map.get(page_id)
            if content:  # Checks for non-empty string
                excerpts.append(content)
                successful_fetches += 1
            elif content is None:
                logger.warning(f"Failed to fetch content for page {page_id} (matched by filter)")

        if not excerpts:
            logger.info(f"Found {len(pages)} pages matching filter, but none had extractable text or fetch failed.")
            return ""

        logger.info(f"Successfully extracted text from {successful_fetches} out of {len(pages)} pages matching filter.")
        return "\n\n---\n\n".join(excerpts)  # Use distinct separator

    def get_excerpts_by_multi_select_tag(
            self,
            database_id: str,
            tag_name: str,
            tag_property_name: str = "Tags"  # Often "Tags", but configurable
    ) -> Optional[str]:
        """
        Fetches all pages in a database containing a specific tag (multi-select)
        and concatenates their plain text content.

        Args:
            database_id: The ID of the Notion database.
            tag_name: The name of the tag to filter by.
            tag_property_name: The name of the multi-select property in Notion (default: "Tags").

        Returns:
            A single string containing the concatenated text from all matching pages,
            separated by '---', or None if an error occurs during querying.
            Returns an empty string if no pages match or matching pages have no text.
        """
        logger.info(
            f"Fetching excerpts for tag '{tag_name}' in database '{database_id}' (property: '{tag_property_name}')")
        filter_params = {
            "property": tag_property_name,
            "multi_select": {"contains": tag_name}
        }

        # Querying database handles its own errors and returns list or []
        pages = self.query_database(database_id, filter_params=filter_params)

        if not pages:
            logger.info(f"No pages found with tag '{tag_name}' in database '{database_id}'.")
            return ""  # No pages match

        excerpts: List[str] = []
        for i, page in enumerate(pages):
            page_id = page.get("id")
            page_title = "Unknown Title"
            # Try to get page title for better logging (assuming standard 'Name' property)
            try:
                title_prop = page.get("properties", {}).get("Name", {}).get("title", [])
                if title_prop:
                    page_title = title_prop[0].get("plain_text", "Unknown Title")
            except Exception:
                pass  # Ignore errors getting title

            if page_id:
                logger.debug(f"Processing page {i + 1}/{len(pages)}: ID '{page_id}', Title '{page_title}'")
                excerpt = self.get_page_plain_text(page_id)
                if excerpt:  # Only add if text was actually extracted
                    excerpts.append(excerpt)
                else:
                    logger.debug(f"Page '{page_id}' ('{page_title}') had no extractable text.")
            else:
                logger.warning(f"Page data missing ID in query results: {page}")

        if not excerpts:
            logger.info(f"Found {len(pages)} pages with tag '{tag_name}', but none had extractable text.")
            return ""

        logger.info(f"Successfully extracted text from {len(excerpts)} out of {len(pages)} pages tagged '{tag_name}'.")
        # Join non-empty excerpts
        return "\n\n---\n\n".join(excerpts)  # Use more distinct separator


# --- Basic Testing/Example Usage ---
if __name__ == '__main__':
    # Configure logging for detailed output when running directly
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running NotionHelper standalone tests...")
    business_db_id = "1645f1f4ce2b8007b322f8a58f5f2b2b"

    try:
        helper = NotionHelper()  # Assumes NOTION_API_KEY is set in .env

        # --- Test 1: Query Database (without filters first) ---
        print("\n--- Testing Database Query (No Filter) ---")
        all_pages = helper.query_database(business_db_id)
        if all_pages:
            print(f"Found {len(all_pages)} pages in the database.")
            # Get ID of the first page for the next test
            FIRST_PAGE_ID = all_pages[0].get("id")
            print(f"ID of the first page: {FIRST_PAGE_ID}")
        else:
            print("Could not retrieve pages or database is empty.")
            FIRST_PAGE_ID = None

        # --- Test 2: Get Page Content ---
        print("\n--- Testing Get Page Content ---")
        if FIRST_PAGE_ID:
            print(f"Attempting to get content for page: {FIRST_PAGE_ID}")
            page_content = helper.get_page_plain_text(FIRST_PAGE_ID)
            if page_content is not None:  # Check for None explicitly in case of error
                print(f"Page Content (first 500 chars):\n---\n{page_content[:500]}...\n---")
            else:
                print("Failed to retrieve content for the first page.")
        else:
            print("Skipping page content test as no page ID was retrieved.")

        # --- Test 3: Get Excerpts by Tag ---
        print("\n--- Testing Get Excerpts by General Filter ---")
        print(f"Attempting to get excerpts using filter: ")
        filtered_excerpts = helper.get_excerpts_by_filter(
            database_id=business_db_id,
            filter_params={
                "property": "Name",
                "rich_text": {
                    "contains": "Fishing"
                }
            }
        )
        if filtered_excerpts is not None:
            if filtered_excerpts:
                print(f"Filtered Excerpts (first 1000 chars):\n---\n{filtered_excerpts[:1000]}...\n---")
            else:
                print("No pages found matching the filter or they had no text.")
        else:
            print("Failed to retrieve excerpts using the filter (check logs).")

        # --- Test 5: Test Get Excerpts by Tag (now uses the wrapper) ---
        print("\n--- Testing Get Excerpts by Tag (Convenience Wrapper) ---")
        print(f"Attempting to get excerpts for tag  ...")
        tagged_excerpts = helper.get_excerpts_by_multi_select_tag(
            database_id=business_db_id,
            tag_property_name="Doc Type",
            tag_name="Details",
        )
        if tagged_excerpts is not None:  # Check for None explicitly
            if tagged_excerpts:
                print(f"Concatenated Excerpts (first 1000 chars):\n---\n{tagged_excerpts[:1000]}...\n---")
            else:
                print(f"No pages found with tag or they contained no extractable text.")
        else:
            print(f"Failed to retrieve excerpts for tag. Check logs for errors.")

        print("\n--- NotionHelper tests completed. ---")

    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
    except ConnectionError as e:
        logger.error(f"Could not connect or initialize client: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
