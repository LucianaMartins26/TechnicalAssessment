import os
import logging
import requests
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import Optional

log_dir = "../log"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"file_downloader.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)


def download_and_extract_zip(download_link: str) -> Optional[str]:
    """Download the ZIP file from the link and extract the XML file."""
    try:
        logging.info(f"Downloading ZIP file from: {download_link}")

        response = requests.get(download_link)

        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
            zip_file.extractall('../downloaded_files')
            logging.info(f"Extracted the ZIP contents to '../downloaded_files/'")

            extracted_files = zip_file.namelist()
            logging.info(f"Extracted files: {extracted_files}")

            for file in extracted_files:
                if file.endswith('.xml'):
                    return file

    except requests.RequestException as e:
        logging.error(f"Failed to download ZIP file: {e}")
    except zipfile.BadZipFile as e:
        logging.error(f"Failed to extract ZIP file (bad file): {e}")


def parse_xml(xml_content: bytes) -> Optional[str]:
    """Parse the XML and find the second download link with file_type 'DLTINS'."""
    try:
        root = ET.fromstring(xml_content)
        dltins_links = []

        for doc in root.findall('.//doc'):
            file_type = None
            download_link = None

            for str_elem in doc.findall("str"):
                if str_elem.attrib['name'] == 'file_type' and str_elem.text == 'DLTINS':
                    file_type = str_elem.text
                if str_elem.attrib['name'] == 'download_link':
                    download_link = str_elem.text

            if file_type == 'DLTINS' and download_link:
                dltins_links.append(download_link)

        logging.info(f"Found {len(dltins_links)} 'DLTINS' download links.")

        if len(dltins_links) >= 2:
            logging.info(f"Returning the second 'DLTINS' link: {dltins_links[1]}")
            return dltins_links[1]
        else:
            logging.warning("Less than 2 'DLTINS' links found.")
            return None

    except ET.ParseError as e:
        logging.error(f"Error parsing XML data: {e}")
        return None


class FileDownloader:

    def __init__(self, url: str) -> None:
        self.url = url

        os.makedirs('../downloaded_files', exist_ok=True)

    def fetch_xml(self) -> Optional[bytes]:
        """Fetch the XML data from the provided URL."""
        try:
            logging.info(f"Fetching XML data from: {self.url}")
            response = requests.get(self.url)
            return response.content
        except requests.RequestException as e:
            logging.error(f"Failed to fetch XML data: {e}")
            return None

    def run(self) -> Optional[str]:
        """Fetch the XML, parse it for DLTINS links, and download/extract the corresponding ZIP."""
        xml_content = self.fetch_xml()
        if xml_content:
            download_link = parse_xml(xml_content)
            if download_link:
                extracted_file = download_and_extract_zip(download_link)
                if extracted_file:
                    logging.info(f"Extracted XML file: {extracted_file}")
                    return extracted_file
                else:
                    logging.error("No XML file was extracted from the ZIP.")
                    return None
            else:
                logging.error("No valid download link found.")
                return None
        else:
            logging.error("Failed to fetch XML content.")
            return None
