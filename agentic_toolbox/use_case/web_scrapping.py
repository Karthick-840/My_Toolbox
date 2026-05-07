import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return None

def extract_investor_relations_url(base_url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Assuming the investor relations link contains the text "Investor Relations"
    link = soup.find('a', string=lambda text: 'Investor Relations' in text if text else False)
    if link:
        return urljoin(base_url, link['href'])
    else:
        print("Investor Relations page not found.")
        return None

def download_pdfs(base_url, html_content, download_folder='pdfs'):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf_links = soup.find_all('a', href=lambda href: href and href.endswith('.pdf'))
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    for link in pdf_links:
        pdf_url = urljoin(base_url, link['href'])
        pdf_name = os.path.join(download_folder, os.path.basename(link['href']))
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with open(pdf_name, 'wb') as pdf_file:
                pdf_file.write(response.content)
            print(f"Downloaded: {pdf_name}")
        else:
            print(f"Failed to download: {pdf_url}")

def main():
    url = 'https://www.itcportal.com/'  # Replace with the target website URL
    html_content = fetch_html(url)
    if html_content:
        investor_relations_url = extract_investor_relations_url(url, html_content)
        if investor_relations_url:
            print(f"Investor Relations Page URL: {investor_relations_url}")
            investor_relations_html = fetch_html(investor_relations_url)
            if investor_relations_html:
                download_pdfs(investor_relations_url, investor_relations_html)

if __name__ == "__main__":
    main()
