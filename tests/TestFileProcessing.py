import unittest
from io import StringIO
from unittest.mock import patch, mock_open

from FileProcessing import FileProcessing


class TestFileProcessing(unittest.TestCase):

    @patch('fsspec.open', new_callable=mock_open)
    def test_convert_to_csv_success(self, mock_fsspec_open):
        """Test the XML-to-CSV conversion with a mock XML file."""
        mock_xml_content = """<?xml version="1.0"?>
        <Document xmlns="urn:iso:std:iso:20022:tech:xsd:auth.036.001.02">
            <FinInstrm>
                <ModfdRcrd>
                    <FinInstrmGnlAttrbts>
                        <Id>ABC123</Id>
                        <FullNm>Test Instrument</FullNm>
                        <ClssfctnTp>XXX</ClssfctnTp>
                        <CmmdtyDerivInd>false</CmmdtyDerivInd>
                        <NtnlCcy>USD</NtnlCcy>
                    </FinInstrmGnlAttrbts>
                    <Issr>TestIssuer</Issr>
                </ModfdRcrd>
            </FinInstrm>
        </Document>"""

        # Mocking reading of XML file
        with patch('builtins.open', mock_open(read_data=mock_xml_content)):
            processor = FileProcessing('test.xml')

            # Mocking the fsspec open function to test file writing
            processor.convert_to_csv()

            # Assert the CSV was written successfully
            mock_fsspec_open.assert_called_with('../output/test.csv', mode='w', newline='', encoding='utf-8')

            handle = mock_fsspec_open()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            expected_csv_content = """FinInstrmGnlAttrbts.Id,FinInstrmGnlAttrbts.FullNm,
            FinInstrmGnlAttrbts.ClssfctnTp,FinInstrmGnlAttrbts.CmmdtyDerivInd,FinInstrmGnlAttrbts.NtnlCcy,
            Issr\nABC123,Test Instrument,XXX,false,USD,TestIssuer\n"""
            self.assertEqual(written_content, expected_csv_content)

    @patch('fsspec.open', new_callable=mock_open)
    def test_column_assessment(self, mock_fsspec_open):
        """Test the column assessment by adding 'a_count' and 'contains_a'."""
        mock_csv_content = """FinInstrmGnlAttrbts.Id,FinInstrmGnlAttrbts.FullNm,FinInstrmGnlAttrbts.ClssfctnTp, 
        FinInstrmGnlAttrbts.CmmdtyDerivInd,FinInstrmGnlAttrbts.NtnlCcy,Issr ABC123,Test Instrument,XXX,false,USD, 
        TestIssuer"""

        # Mocking reading of CSV file
        with patch('builtins.open', mock_open(read_data=mock_csv_content)):
            processor = FileProcessing('test.xml')

            # Simulate reading and writing the CSV with fsspec
            mock_fsspec_open.return_value = StringIO(mock_csv_content)
            processor.output_path = '../output/test.csv'  # mock output path

            processor.column_assessment()

            # Assert that the CSV was written with the new columns
            mock_fsspec_open.assert_called_with('../output/test.csv', mode='w', newline='', encoding='utf-8')

            handle = mock_fsspec_open()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            expected_csv_content = """FinInstrmGnlAttrbts.Id,FinInstrmGnlAttrbts.FullNm,
            FinInstrmGnlAttrbts.ClssfctnTp,FinInstrmGnlAttrbts.CmmdtyDerivInd,FinInstrmGnlAttrbts.NtnlCcy,Issr,
            a_count,contains_a ABC123,Test Instrument,XXX,false,USD,TestIssuer,1,YES"""
            self.assertEqual(written_content, expected_csv_content)

    @patch('fsspec.open', new_callable=mock_open)
    def test_run_method(self, mock_fsspec_open):
        """Test the entire run process including CSV conversion and column assessment."""
        mock_xml_content = """<?xml version="1.0"?>
        <Document xmlns="urn:iso:std:iso:20022:tech:xsd:auth.036.001.02">
            <FinInstrm>
                <ModfdRcrd>
                    <FinInstrmGnlAttrbts>
                        <Id>ABC123</Id>
                        <FullNm>Test Instrument</FullNm>
                        <ClssfctnTp>XXX</ClssfctnTp>
                        <CmmdtyDerivInd>false</CmmdtyDerivInd>
                        <NtnlCcy>USD</NtnlCcy>
                    </FinInstrmGnlAttrbts>
                    <Issr>TestIssuer</Issr>
                </ModfdRcrd>
            </FinInstrm>
        </Document>"""

        mock_csv_content = """FinInstrmGnlAttrbts.Id,FinInstrmGnlAttrbts.FullNm,FinInstrmGnlAttrbts.ClssfctnTp,
        FinInstrmGnlAttrbts.CmmdtyDerivInd,FinInstrmGnlAttrbts.NtnlCcy,Issr ABC123,Test Instrument,XXX,false,USD,
        TestIssuer"""

        # Mocking reading of XML and CSV file
        with patch('builtins.open', mock_open(read_data=mock_xml_content)):
            processor = FileProcessing('test.xml')

            # Mocking fsspec for reading and writing files
            mock_fsspec_open.side_effect = [StringIO(mock_xml_content), StringIO(mock_csv_content), mock_open()]

            processor.run()

            # Check that both convert_to_csv and column_assessment processed and wrote files
            self.assertEqual(mock_fsspec_open.call_count, 3)

            # Assert that the CSV was written with the new columns
            handle = mock_fsspec_open()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            expected_csv_content = """FinInstrmGnlAttrbts.Id,FinInstrmGnlAttrbts.FullNm,
            FinInstrmGnlAttrbts.ClssfctnTp,FinInstrmGnlAttrbts.CmmdtyDerivInd,FinInstrmGnlAttrbts.NtnlCcy,Issr,
            a_count,contains_a ABC123,Test Instrument,XXX,false,USD,TestIssuer,1,YES"""
            self.assertEqual(written_content, expected_csv_content)
