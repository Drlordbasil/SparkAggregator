import requests
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import datetime
from openai import ChatCompletion


class WebScraper:
    def __init__(self):
        self.search_queries = []
        self.search_results = []
        self.content_database = []
        self.categorized_content = {}
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.kmeans = KMeans(n_clusters=5, random_state=0)
        self.chat_completion = ChatCompletion.create(model="gpt-3.5-turbo")

    def prompt_user_search_queries(self):
        num_search_queries = int(input("Enter the number of search queries: "))
        for _ in range(num_search_queries):
            search_query = input("Enter the search query: ")
            self.search_queries.append(search_query)

    def generate_search_results(self):
        for query in self.search_queries:
            url = f"https://www.google.com/search?q={query}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.find_all('a')
            self.search_results.extend(search_results)

    def extract_content(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        article_title = soup.find('h1').text
        article_summary = soup.find('p').text
        publication_date = datetime.datetime.now()
        article_info = {
            'title': article_title,
            'summary': article_summary,
            'publication_date': publication_date,
            'url': url
        }
        self.content_database.append(article_info)

    def store_content(self):
        df = pd.DataFrame(self.content_database)
        df.to_csv('content_database.csv', index=False)

    def load_content(self):
        df = pd.read_csv('content_database.csv')
        self.content_database = df.to_dict('records')

    def categorize_content(self):
        for content in self.content_database:
            article_summary = content['summary']
            category = self.get_category(article_summary)
            if category not in self.categorized_content:
                self.categorized_content[category] = []
            self.categorized_content[category].append(content)

    def get_category(self, article_summary):
        X = self.vectorizer.fit_transform([article_summary])
        self.kmeans.fit(X)
        return self.kmeans.predict(X)[0]

    def assign_tags(self):
        self.article_tags = {}
        for category, content_list in self.categorized_content.items():
            tags = []
            for content in content_list:
                article_summary = content['summary']
                tags.append(self.get_tags(article_summary))
            self.article_tags[category] = tags

    def get_tags(self, article_summary):
        response = self.chat_completion.create(
            messages=[
                {"role": "system", "content": "You are an AI model."},
                {"role": "user", "content": article_summary},
                {"role": "assistant", "content": ""}
            ]
        )
        return response.choices[0].message.content

    def update_content(self):
        new_urls = []
        for query in self.search_queries:
            url = f"https://www.google.com/search?q={query}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.find_all('a')
            new_urls.extend([result['href']
                            for result in search_results if result.get('href')])

        unique_urls = set(new_urls)
        for url in unique_urls:
            if url not in [content['url'] for content in self.content_database]:
                self.extract_content(url)


class UserInterface:
    def __init__(self):
        self.web_scraper = WebScraper()

    def execute_web_scraper(self):
        self.web_scraper.prompt_user_search_queries()
        self.web_scraper.generate_search_results()
        self.web_scraper.store_content()
        self.web_scraper.load_content()
        self.web_scraper.categorize_content()
        self.web_scraper.assign_tags()
        self.web_scraper.update_content()

    def run(self):
        print("===== User Interface =====")
        print("1. Execute Web Scraper")
        print("2. Exit")
        while True:
            try:
                choice = int(input("Enter your choice: "))
                if choice == 1:
                    self.execute_web_scraper()
                elif choice == 2:
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid choice. Please try again.")

        print("Exiting user interface.")


def main():
    user_interface = UserInterface()
    user_interface.run()


if __name__ == "__main__":
    main()
