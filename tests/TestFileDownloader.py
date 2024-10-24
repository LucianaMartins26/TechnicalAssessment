import unittest
from unittest.mock import patch, mock_open, MagicMock
import requests
import zipfile

from FileDownloader import FileDownloader, download_and_extract_zip, parse_xml


class TestFileDownloader(unittest.TestCase):

    @patch('requests.get')
    def test_fetch_xml_success(self, mock_get):
        """Test fetching XML data from a URL successfully."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = (b"<root><doc><str name='file_type'>DLTINS</str><str "
                                         b"name='download_link'>httpss://example.com/download.zip</str></doc></root>")

        downloader = FileDownloader("httpss://example.com/test.xml")
        xml_content = downloader.fetch_xml()

        self.assertIsNotNone(xml_content)
        self.assertEqual(xml_content,
                         b"<root><doc><str name='file_type'>DLTINS</str><str "
                         b"name='download_link'>httpss://example.com/download.zip</str></doc></root>")

    @patch('requests.get')
    def test_fetch_xml_failure(self, mock_get):
        """Test handling of failed XML fetch due to a network error."""
        mock_get.side_effect = requests.RequestException("Network error")

        downloader = FileDownloader("https://example.com/test.xml")
        xml_content = downloader.fetch_xml()

        self.assertIsNone(xml_content)

    def test_parse_xml_success(self):
        """Test parsing the XML and extracting the second DLTINS link."""
        xml_data = b"""
        <root>
            <doc>
                <str name='file_type'>DLTINS</str>
                <str name='download_link'>https://example.com/download1.zip</str>
            </doc>
            <doc>
                <str name='file_type'>DLTINS</str>
                <str name='download_link'>https://example.com/download2.zip</str>
            </doc>
        </root>
        """
        second_link = parse_xml(xml_data)

        self.assertEqual(second_link, "https://example.com/download2.zip")

    def test_parse_xml_no_second_link(self):
        """Test parsing XML with less than two DLTINS links."""
        xml_data = b"""
        <root>
            <doc>
                <str name='file_type'>DLTINS</str>
                <str name='download_link'>https://example.com/download1.zip</str>
            </doc>
        </root>
        """
        second_link = parse_xml(xml_data)

        self.assertIsNone(second_link)

    @patch('requests.get')
    @patch('zipfile.ZipFile')
    def test_download_and_extract_zip(self, mock_zipfile, mock_get):
        """Test downloading and extracting a ZIP file."""
        # Simulate a successful download of a zip file
        mock_get.return_value.content = b"fake zip content"

        # Simulate the behavior of zipfile.ZipFile
        mock_zip = MagicMock()
        mock_zip.namelist.return_value = ['test.xml']
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        with patch('builtins.open', mock_open()):
            extracted_file = download_and_extract_zip("https://example.com/download.zip")

        mock_get.assert_called_once_with("https://example.com/download.zip")
        mock_zipfile.assert_called_once()
        self.assertEqual(extracted_file, 'test.xml')

    @patch('requests.get')
    @patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile)
    def test_download_and_extract_bad_zip(self, mock_zipfile, mock_get):
        """Test handling a bad ZIP file during extraction."""
        # Simulate a successful download but with a bad zip file
        mock_get.return_value.content = b"fake bad zip content"

        extracted_file = download_and_extract_zip("https://example.com/download.zip")

        self.assertIsNone(extracted_file)
        mock_get.assert_called_once_with("https://example.com/download.zip")
        mock_zipfile.assert_called_once()

    @patch('requests.get')
    @patch('zipfile.ZipFile')
    def test_file_downloader_run_success(self, mock_zipfile, mock_get):
        """Test the full run of the FileDownloader class successfully."""
        # Simulate successful XML fetch
        mock_get.side_effect = [
            MagicMock(status_code=200, content=b"""
            <root>
                <doc>
                    <str name='file_type'>DLTINS</str>
                    <str name='download_link'>https://example.com/download1.zip</str>
                </doc>
                <doc>
                    <str name='file_type'>DLTINS</str>
                    <str name='download_link'>https://example.com/download2.zip</str>
                </doc>
            </root>
            """),
            MagicMock(content=b"fake zip content")
        ]

        # Simulate successful ZIP extraction
        mock_zip = MagicMock()
        mock_zip.namelist.return_value = ['test.xml']
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        downloader = FileDownloader("https://example.com/test.xml")
        extracted_file = downloader.run()

        self.assertEqual(extracted_file, 'test.xml')

    @patch('requests.get', side_effect=requests.RequestException("Network error"))
    def test_file_downloader_run_fail_fetch(self, mock_get):
        """Test the failure of fetching the initial XML during the run method."""
        downloader = FileDownloader("https://example.com/test.xml")
        extracted_file = downloader.run()

        self.assertIsNone(extracted_file)
