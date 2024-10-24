import os
import re
import logging
import csv
import pandas as pd
import fsspec
import xml.etree.ElementTree as ET

log_dir = "../log"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"file_processing.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)


def get_base_filename(file: str) -> str:
    """Extract the base filename without the extension."""
    base_name = file.split('.')[0]
    return base_name


class FileProcessing:

    def __init__(self, xml_file: str) -> None:

        self.xml_file = xml_file
        self.output_path = None

        with open(f'../downloaded_files/{self.xml_file}', 'r', encoding='utf-8') as f:
            content = f.read()

        self.namespaces = dict(re.findall(r'xmlns:([a-zA-Z0-9]+)="([^"]+)"', content))

    def convert_to_csv(self) -> None:
        """Process the XML file and convert its contents into a CSV file."""

        try:
            logging.info(f"Processing XML file: {self.xml_file}")

            tree = ET.parse(os.path.join('../downloaded_files', self.xml_file))
            root = tree.getroot()

            os.makedirs('../output', exist_ok=True)

            self.output_path = f'../output/{get_base_filename(self.xml_file)}.csv'

            with open(self.output_path, mode='w', newline='') as file:
                writer = csv.writer(file)

                writer.writerow([
                    'FinInstrmGnlAttrbts.Id',
                    'FinInstrmGnlAttrbts.FullNm',
                    'FinInstrmGnlAttrbts.ClssfctnTp',
                    'FinInstrmGnlAttrbts.CmmdtyDerivInd',
                    'FinInstrmGnlAttrbts.NtnlCcy',
                    'Issr'
                ])

                for fin_instrm in root.findall('.//FinInstrm'):
                    fin_instrm_id = fin_instrm.findtext('.//Id')
                    fin_instrm_fullnm = fin_instrm.findtext('.//FullNm')
                    fin_instrm_clssfctntp = fin_instrm.findtext('.//ClssfctnTp')
                    fin_instrm_cmmdty_deriv_ind = fin_instrm.findtext('.//CmmdtyDerivInd')
                    fin_instrm_ntnl_ccy = fin_instrm.findtext('.//NtnlCcy')
                    issr = fin_instrm.findtext('.//Issr')

                    writer.writerow([
                        fin_instrm_id,
                        fin_instrm_fullnm,
                        fin_instrm_clssfctntp,
                        fin_instrm_cmmdty_deriv_ind,
                        fin_instrm_ntnl_ccy,
                        issr
                    ])

        except ET.ParseError as e:
            logging.error(f"Error parsing XML file: {e}")
        except Exception as e:
            logging.error(f"Error during CSV conversion: {e}")

    def column_assessment(self) -> None:
        """Add new columns 'a_count' and 'contains_a' to the CSV file."""

        try:
            with fsspec.open(self.output_path, mode='r', newline='', encoding='utf-8') as file:
                df = pd.read_csv(file)

            df['a_count'] = df['FinInstrmGnlAttrbts.FullNm'].apply(lambda x: x.count('a') if pd.notnull(x) else 0)
            logging.info("'a_count' column added successfully.")

            df['contains_a'] = df['a_count'].apply(lambda x: 'YES' if x > 0 else 'NO')
            logging.info("'contains_a' column added successfully.")

            with fsspec.open(self.output_path, mode='w', newline='', encoding='utf-8') as file:
                df.to_csv(file, index=False)
            logging.info(f"Updated CSV file saved successfully at: {self.output_path}")

        except Exception as e:
            logging.error(f"Error while processing CSV: {e}")

    def run(self):
        self.convert_to_csv()
        self.column_assessment()

        return self.output_path
