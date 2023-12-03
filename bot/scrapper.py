from typing import List, Any, Union
import requests
from bs4 import BeautifulSoup
import asyncio


from langchain.document_loaders import WebBaseLoader
from langchain.docstore.document import Document


def _build_metadata(soup: Any, url: str) -> dict:
    """Build metadata from BeautifulSoup output."""
    metadata = {"source": url}
    if title := soup.find("title"):
        metadata["title"] = title.get_text()
    if description := soup.find("meta", attrs={"name": "description"}):
        metadata["description"] = description.get("content", None)
    if html := soup.find("html"):
        metadata["language"] = html.get("lang", None)
    return metadata


def get_all_urls(url: str, domain: bool = True):
    response = requests.get(url)
    html_content = response.content
    soup = BeautifulSoup(html_content, 'html.parser')
    sub_links = []
    for link in soup.find_all('a'):
        print
        href = link.get('href')
        if href is not None:
            sub_links.append(href)

    main_links = []
    for link in sub_links:
        if link.startswith('/'):
            full_path = link
            if domain:
                full_path = f"{url.rstrip('/')}{link}"
            
            main_links.append(full_path)
        
    return main_links


class CustomWebBaseLoader(WebBaseLoader):

    def load(self) -> List[Document]:
        """Load text from the url(s) in web_path."""
        docs = []
        results = ""
        for path in self.web_paths:
            soup = self._scrape(path)
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            results = "\n".join(chunk for chunk in chunks if chunk)
            metadata = _build_metadata(soup, path)
            docs.append(Document(page_content=results, metadata=metadata))
        
        return docs
    

    async def aload(self) -> List[Document]:
        """Load text from the urls in web_path async into Documents."""

        results = await self.scrape_all(self.web_paths)
        docs = []
        responses = ""
        for i in range(len(results)):
            soup = results[i]
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            responses = "\n".join(chunk for chunk in chunks if chunk)
            metadata = _build_metadata(soup, self.web_paths[i])
            docs.append(Document(page_content=responses, metadata=metadata))

        return docs
    

    async def scrape_all(self, urls: List[str], parser: Union[str, None] = None) -> List[Any]:
        """Fetch all urls, then return soups for all results."""
        results = await self.fetch_all(urls)
        final_results = []
        for i, result in enumerate(results):
            url = urls[i]
            if parser is None:
                if url.endswith(".xml"):
                    parser = "xml"
                else:
                    parser = self.default_parser
                self._check_parser(parser)
            final_results.append(BeautifulSoup(result, parser))

        return final_results