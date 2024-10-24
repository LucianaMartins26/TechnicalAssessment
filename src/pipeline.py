from FileProcessing import FileProcessing
from FileDownloader import FileDownloader


def pipeline(url):
    download = FileDownloader(url)
    extracted_file = download.run()

    if extracted_file:
        processor = FileProcessing(extracted_file)
        processor.run()


if __name__ == '__main__':
    pipeline('https://registers.esma.europa.eu/solr/esma_registers_firds_files/select?q=*&fq=publication_date:%5B2021'
             '-01-17T00:00:00Z+TO+2021-01-19T23:59:59Z%5D&wt=xml&indent=true&start=0&rows=100')
