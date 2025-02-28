
import base64
import json
import os
import sys


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

class Printer():

    def __init__(self):  
        

        self.pages = []
        self.print_options = self._set_print_options()
        self.plugin_path = os.path.dirname(os.path.realpath(__file__))

    def add_page(self, page, config):

        temp_page_path = page.file.url.rsplit('/', 1)[0]

        pdf_path = os.path.join(config["site_dir"], "pdfs", temp_page_path)
        os.makedirs(pdf_path, exist_ok=True)
        pdf_file = os.path.join(pdf_path, page.file.name) + ".pdf"

        relpath = os.path.relpath(pdf_file, os.path.dirname(page.file.abs_dest_path))

        page_paths = {
            "name": page.file.name,
            "url": "file://" + page.file.abs_dest_path,
            "pdf_file": pdf_file,
            "relpath": relpath,
        }

        self.pages.append(page_paths)
        return page_paths

    def add_download_link(self, output_content, page_paths):

        soup = BeautifulSoup(output_content, 'html.parser')
        soup = self._add_style(soup)
        soup = self._add_link(soup, page_paths)
        
        return str(soup)
    
    def add_Cover_Page(self, output_content, cover_template):
        
        if cover_template != "":
            cover_template = f'<article class="print-first-page" > {cover_template} </article>'
            soup_cover_template = BeautifulSoup(cover_template, "html.parser")

            soup = BeautifulSoup(output_content, 'html.parser')
            soup.article.insert_before(soup_cover_template)
            return str(soup)

        return output_content

    def _add_style(self, soup):

        stylesheet = os.path.join(self.plugin_path, "stylesheets", "printer.css")
        with open(stylesheet, 'r') as file:
            style = file.read()
        
        if not soup.style:
            head = soup.head
            head.append(soup.new_tag('style', type='text/css'))
        soup.style.append(style)
        return soup

    def _add_link(self, soup, page_paths):

        a = soup.new_tag("a", href=page_paths["relpath"])
        a.string = "Download PDF"
        div = soup.new_tag("div")
        div['class'] = 'download-btn'
        div.append(a)
        
        if not soup.article:
            soup.append(soup.new_tag('article'))
        soup.article.insert(0, div)
        return soup

    def print_pages(self):

        driver = self._create_driver()

        for page in self.pages:
            self.print_to_pdf(driver, page)

        driver.quit()

    def print_to_pdf(self, driver, page):

        print(f"[pdf-with-js] - printing '{page['name']}' to file...")

        driver.get(page["url"])
        result = self._send_devtools_command(driver, "Page.printToPDF", self.print_options)

        self._write_file(result['data'], page["pdf_file"])

    def _create_driver(self):
        webdriver_options = webdriver.ChromeOptions()

        webdriver_options.add_argument('--headless')
        webdriver_options.add_argument('--disable-gpu')
        webdriver_options.add_argument('--no-sandbox')
        webdriver_options.add_argument('--disable-dev-shm-usage')
        webdriver_options.add_argument('--disable-web-security')
        webdriver_options.add_argument('--ignore-certificate-errors-spki-list')
        webdriver_options.add_argument('--allow-file-access-from-files')
        webdriver_options.add_argument('--allow-insecure-localhost')
        
        return webdriver.Remote(command_executor='http://chrome:4444/wd/hub', options=webdriver_options,)

    def _set_print_options(self):

        return {
            'landscape': False,
            'displayHeaderFooter': True,
            'footerTemplate': '<div style="font-size:8px; margin:auto;">'
                              'Page <span class="pageNumber"></span> '
                              'of <span class="totalPages"></span></div>',
            'printBackground': True,
            'preferCSSPageSize': True,
        }

    def _send_devtools_command(self, driver, cmd, params={}):

        resource = f"/session/{driver.session_id}/chromium/send_command_and_get_result"
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)
        return response.get('value')

    def _write_file(self, b64_data, name):

        data = base64.b64decode(b64_data)
        with open(name, 'wb') as file:
            file.write(data)
