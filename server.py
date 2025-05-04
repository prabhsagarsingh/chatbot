from typing import Any
from mcp.server.fastmcp import FastMCP
from pathlib import Path
from datetime import datetime
from collections import Counter
from pathlib import Path
from win10toast import ToastNotifier
from urllib.parse import quote_plus 

import os
import aiofiles
import csv
import datetime
import webbrowser
import logging

mcp = FastMCP("chatbot")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@mcp.tool()
async def add_log_to_journal(year: str, month: str, date: str, mood: str, log: str):
    """
       A utility function for recording personal mood and journal entries in a structured format, 
    useful for building mood trackers, journaling apps, or mental health dashboards.

    This function can be used in any application where users want to log emotional states 
    along with reflections or notes, organized by year and month. It enables seamless tracking 
    of mood trends over time and supports further analysis or visualization of emotional patterns.


    Args:
        year (str): The year of the journal entry (e.g., "2025"). 
                    Used to organize logs chronologically into yearly folders.

        month (str): The month of the journal entry (e.g., "May").
                     Used to organize logs into monthly subfolders and files.
                     Also forms the base of the CSV filename (e.g., "May_journal_log.csv").

        date (str): The specific date of the entry in a readable format (e.g., "2025-05-04").
                    This value is logged in the CSV under the "Date" column.

        mood (str): A brief mood descriptor (e.g., "Happy", "Anxious", "Tired").
                    This value is stored in the "Mood" column and helps track emotional trends.

        log (str): The actual journal entry text, containing thoughts, reflections, or events.
                   This is saved under the "Log" column of the CSV.

    Example entry added to the CSV:
        Date,Mood,Log
        2025-05-01,Tired,"Didn't sleep well last night. Felt groggy all day at work."
2025-05-02,Content,"Had a peaceful day. Finished reading a book and took a long walk."
2025-05-03,Anxious,"Upcoming deadline is stressing me out. Need to plan better."
2025-05-04,Happy,"Had a productive day and went for a run."
2025-05-05,Sad,"Feeling down without any particular reason. Hoping tomorrow is better."
2025-05-06,Excited,"Booked tickets for the summer trip! Can't wait to travel."
2025-05-07,Frustrated,"Laptop crashed during a meeting. Lost some work progress."
2025-05-08,Grateful,"Had dinner with family. Feeling thankful for small moments."
2025-05-09,Calm,"Spent the evening meditating and doing yoga. Very relaxing."
2025-05-10,Motivated,"Woke up early, cleaned the apartment, and hit all my to-dos."
        2025-05-04,Happy,"Had a productive day and went for a run."

    Returns:
        None
    """
    
    base_path = Path(__file__).parent
    log_dir = base_path / "data" / "journal" / year / month
    log_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{month}_journal_log.csv"
    log_file = log_dir / filename
    file_exists = log_file.exists()

    # Escape double quotes and wrap in quotes for CSV cell safety
    def escape_log_field(text: str) -> str:
        text = text.replace('"', '""')  # Escape internal quotes
        return f'"{text}"'  # Wrap entire entry in quotes

    headers = ["Date", "Mood", "Log"]
    row = [date, mood, escape_log_field(log)]

    async with aiofiles.open(log_file, mode="a", encoding="utf-8") as f:
        if not file_exists:
            await f.write(",".join(headers) + "\n")
        await f.write(",".join(row) + "\n")

@mcp.tool()
async def analyze_mood_trend(from_date: str, to_date: str) -> str:
    """
    A utility function to analyze mood trends over a specified date range based on journal entries.

    This function reads CSV journal logs saved using the `add_log_to_journal` function,
    filters the logs that fall within the given date range, and calculates the frequency
    of each mood. It is useful for mental health tracking apps or dashboards aiming to
    give users insights into their emotional patterns over time.

    Args:
        from_date (str): The start of the date range in the format "YYYY-MM-DD".
                         Only entries from this date onward will be included in the analysis.

        to_date (str): The end of the date range in the format "YYYY-MM-DD".
                       Only entries up to this date (inclusive) will be included in the analysis.

    Returns:
        str: A summary string of mood frequencies during the selected period.
             Example: "Mood trend from 2025-05-01 to 2025-05-10: Happy (2), Anxious (1), Calm (1)"
    """

    base_path = Path(__file__).parent
    data_path = base_path / "data" / "journal"

    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")

    mood_counter = Counter()

    # Traverse through all year and month folders
    for year_dir in data_path.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue

        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue

            # Construct the CSV file path
            csv_file = month_dir / f"{month_dir.name}_journal_log.csv"
            if not csv_file.exists():
                continue

            # Read and filter rows based on date range
            async with aiofiles.open(csv_file, mode="r", encoding="utf-8") as f:
                contents = await f.read()
                reader = csv.DictReader(contents.splitlines())
                for row in reader:
                    entry_date = datetime.strptime(row["Date"], "%Y-%m-%d")
                    if from_dt <= entry_date <= to_dt:
                        mood_counter[row["Mood"]] += 1

    if not mood_counter:
        return f"No journal entries found between {from_date} and {to_date}."

    # Format mood summary string
    mood_summary = ", ".join(f"{mood} ({count})" for mood, count in mood_counter.items())
    return f"Mood trend from {from_date} to {to_date}: {mood_summary}"

@mcp.tool()
async def add_log_to_file(filename: str, log: str):
    """
    A general-purpose utility function for appending a text log entry to a specified CSV file.

    This function is useful for various logging needs outside of structured journaling, such as:
    - Daily reflections
    - Event or incident tracking
    - Custom notes related to tasks, productivity, or personal growth

    If the file doesn't exist, it will be created with a default header. Each log entry is
    timestamped with the current date and time, making it easy to track when each log was added.

    Args:
        filename (str): The name of the file to write to (e.g., "reflections_log.csv").
                        This file will be created inside the "data/logs" directory relative to the script.

        log (str): The log message or reflection text to append to the file.
                   The text is safely escaped to handle commas and quotes.

    Example entry added to the CSV:
        Timestamp,Log
        2025-05-04 22:15:32,"Had a meaningful chat with a friend about future goals."

    Returns:
        None
    """

    

    # Define a base directory for generic logs
    base_path = Path(__file__).parent
    log_dir = base_path / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / filename
    file_exists = log_file.exists()

    # Get the current timestamp in a readable format
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Escape internal quotes and wrap log entry in quotes for CSV safety
    def escape_log_field(text: str) -> str:
        text = text.replace('"', '""')  # Escape double quotes
        return f'"{text}"'

    headers = ["Timestamp", "Log"]
    row = [timestamp, escape_log_field(log)]

    # Append the log entry asynchronously
    async with aiofiles.open(log_file, mode="a", encoding="utf-8") as f:
        if not file_exists:
            await f.write(",".join(headers) + "\n")
        await f.write(",".join(row) + "\n")

@mcp.tool()
async def add_reminder(title: str, message: str):
    """
    A utility function to create a desktop reminder and log it to a CSV file.

    This is useful for building simple reminder systems, productivity tools, or notification
    services. It logs each reminder to a structured CSV file and uses 
    the toast notification system to immediately alert the user.

    Args:
        title (str): The title of the reminder notification (e.g., "Drink Water").
                     This will appear as the headline of the toast notification.

        message (str): The content or body of the reminder (e.g., "Take a break and stretch").
                       This message is both displayed in the notification and saved to the log.

    Returns:
        None
    """


    # Set up timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Set base log file path
    base_path = Path(__file__).parent
    log_dir = base_path / "data" / "reminders"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "reminders_log.csv"
    file_exists = log_file.exists()

    # Escape message text to be safe in CSV (quotes, commas)
    def escape_csv(text: str) -> str:
        text = text.replace('"', '""')  # Escape internal quotes
        return f'"{text}"'

    headers = ["Timestamp", "Title", "Message"]
    row = [timestamp, escape_csv(title), escape_csv(message)]

    # Write to log file asynchronously
    async with aiofiles.open(log_file, mode="a", encoding="utf-8") as f:
        if not file_exists:
            await f.write(",".join(headers) + "\n")
        await f.write(",".join(row) + "\n")

    # Display Windows toast notification
    notifier = ToastNotifier()
    notifier.show_toast(title=title, msg=message, duration=10, threaded=True)

@mcp.tool()
async def search_file_by_name(filename: str, root_dir: str = "C:\\") -> list[str]:
    """
    Searches for files with names similar to the given filename within the root directory.
    
    Uses fuzzy matching to identify likely matches. Useful when the user can't remember exact file names.
    
    Args:
        filename (str): The target filename or partial name to search for.
        root_dir (str): The root directory to start searching from. Defaults to 'C:\\'.

    Returns:
        list[str]: List of full paths to files with similar names.
    """
    logging.info(f"Starting fuzzy file search for '{filename}' under root: {root_dir}")
    
    matched_files = []
    candidates = []

    # Walk through the entire directory tree
    for dirpath, _, files in os.walk(root_dir):
        for file in files:
            candidates.append((file, os.path.join(dirpath, file)))

    logging.info(f"Total candidate files collected: {len(candidates)}")

    # Extract just file names for fuzzy match
    file_names = [name for name, _ in candidates]
    close_matches = get_close_matches(filename, file_names, n=10, cutoff=0.6)

    logging.info(f"Close matches found: {close_matches}")

    # Get the full paths of matched files
    for match in close_matches:
        for candidate_name, full_path in candidates:
            if candidate_name == match:
                matched_files.append(full_path)
                logging.info(f"Match found: {full_path}")

    if not matched_files:
        logging.warning("No matching files found.")

    return matched_file

@mcp.tool()
async def search_web(query: str):
    """
    Opens a new browser tab using the default system browser and performs a web search 
    for the provided query string.

    This function is helpful for automation tools, digital assistants, and personal productivity 
    scripts where the goal is to quickly launch a search in the browser without manually opening it.

    It ensures:
    - URL-safe encoding of the query
    - Use of system's default web browser
    - Logging of the action (success/failure) for monitoring or debugging purposes

    Args:
        query (str): The plain-text string to be searched. This could be a question, keywords, or a topic.

    Example:
        Search for latest new in web => search_duckduckgo("Python asyncio tutorial")
        -> Opens: https://duckduckgo.com/?q=Python+asyncio+tutorial

    Returns:
        None
    """

    try:
        # Convert the plain-text query into a URL-safe encoded format
        # For example, spaces become '+', special characters are escaped
        encoded_query = quote_plus(query)

        # Construct the full DuckDuckGo search URL
        url = f"https://duckduckgo.com/?q={encoded_query}"

        # Attempt to open the URL in a new tab using the system's default web browser
        webbrowser.open_new_tab(url)

     # Log the action to confirm success (useful for debugging or automation logs)
        logging.info(f"[DuckDuckGo Search] Successfully opened search for query: {query}")

    except Exception as e:
        # Log any exceptions that occur (e.g., no browser found, invalid URL, etc.)
        logging.error(f"[DuckDuckGo Search] Failed to open search for query '{query}': {e}")

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

