import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_links(url):
    try:
        # Get HTML content from the URL
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor tags and extract their href attributes
        links = set()
        for a_tag in soup.find_all('a', href=True):
            full_url = urljoin(url, a_tag['href'])  # make relative URLs absolute
            # Only add URLs that start with the specified prefix
            if full_url.startswith("https://taxonomy.legal/terms/"):
                links.add(full_url)

        return list(links)
    
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []

# Example usage
if __name__ == "__main__":
    url = "https://taxonomy.legal/"  # Replace with your target URL
    links = extract_links(url)
    print(f"\nFound {len(links)} taxonomy term links:")
    for link in links:
        print(link)
