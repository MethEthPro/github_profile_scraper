
# GitHub Profile Scraper

A Python-based tool that scrapes GitHub profiles, retrieving detailed user information such as profile metadata, repositories, and followers. This tool leverages the GitHub API and is built to efficiently collect data, even for large profiles, while handling API rate limits.

## Features

- **User Information**: Scrapes profile details like username, bio, location, company, and more.
- **Repository Information**: Fetches details on user repositories, including:
  - Repository names
  - Descriptions
  - Stars, forks, and issues
  - Programming languages used
- **Follower/Following Data**: Retrieves and lists user followers and the people they follow.
- **API Rate Limit Handling**: Includes retry logic for GitHub API requests to respect rate limits.
- **SCORE CALCULATION**: In the end for each repo we try to give it a score depending on its complexities , lines of code, complex sections of code.

## Technologies Used

- **Python**: The core language of the project.
- **GitHub API**: Used to fetch profile and repository data.
- **Requests**: For handling API requests.
- **JSON**: For parsing and storing API responses.

## Installation

1. Clone the repository:
   \`\`\`bash
   git clone https://github.com/MethEthPro/github_profile_scraper.git
   \`\`\`
2. Navigate to the project directory:
   \`\`\`bash
   cd github_profile_scraper
   \`\`\`
3. (Optional) Create and activate a virtual environment:
   \`\`\`bash
   python3 -m venv venv
   source venv/bin/activate  # For Windows, use \`venv\Scripts\activate\`
   \`\`\`
4. Install the required packages:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

## Usage

1. **Set Up GitHub Token**:
   - Generate a GitHub personal access token with the required permissions.
   - Set the token in the environment variables or update the configuration in the project.

2. **Run the Scraper**:
   - Execute the main script to start scraping:
     \`\`\`bash
     python scraper.py
     \`\`\`

3. **Output**:
   - View the scraped data either in the terminal or the JSON output files generated in the project directory.
  
   - ![Screenshot (380)](https://github.com/user-attachments/assets/5cb4fc39-ab4b-430a-be0a-cfaaf66d4183)


### Command-Line Arguments

The scraper accepts the following optional arguments:
- \`--username\`: GitHub username to scrape. Example:
  \`\`\`bash
  python scraper.py --username octocat
  \`\`\`
- \`--rate_limit\`: Customize rate limit handling by specifying the wait time.

For more usage options, run:
\`\`\`bash
python scraper.py --help
\`\`\`

## API Rate Limit Handling

The GitHub API imposes a rate limit on the number of requests that can be made in a specific time frame. This project includes retry logic that automatically pauses and resumes requests based on the rate limits to ensure smooth operation without interruptions.

