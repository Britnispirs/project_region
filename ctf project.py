import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebScanner:
    def __init__(self, target_url):
        self.target_url = target_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        })

    def get_forms(self, url):
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.find_all("form")

    def submit_form(self, form, value, url):
        action = form.get("action")
        post_url = urljoin(url, action)
        method = form.get("method", "get").lower()
        data = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            type = input_tag.get("type", "text")
            if type == "text" or type == "search":
                data[name] = value
            else:
                data[name] = input_tag.get("value", "test")
        if method == "post":
            return self.session.post(post_url, data=data)
        return self.session.get(post_url, params=data)

    def scan_xss(self, url):
        xss_payload = "<script>alert('vulnerable')</script>"
        forms = self.get_forms(url)
        print(f"[+] Найдено форм для проверки XSS: {len(forms)}")
        for form in forms:
            res = self.session.get(target, verify=False, timeout=5)
            if xss_payload in res.text:
                print(f"[!!!] XSS обнаружена в форме на {url}")
                return True
        return False

    def scan_sql_injection(self, url):
            payload = "'"
            print(f"[*] Проверка на SQLi: {url}")
            if not url.endswith('/'):
                target = url + '/' + payload
            else:
                target = url + payload
            try:
                res = self.session.get(target, verify=False, timeout=5)
                errors = ["sql syntax", "mysql_fetch", "near '\"'"]
                
                for err in errors:
                    if err in res.text.lower():
                        print(f"[!!!] Найдена ошибка SQL: {target}")
                        return True
            except:
                print("[-] Ошибка подключения")
            return False

if __name__ == "__main__":
    print("---  ---")
    target = input("Введите URL для сканирования (напр. http://127.0.0.1/): ")
    scanner = WebScanner(target)
    
    print("\n[1] Запуск сканирования на SQL-инъекции...")
    scanner.scan_sql_injection(target)
    
    print("\n[2] Запуск сканирования на XSS...")
    scanner.scan_xss(target)
    
    print("\n--- Сканирование завершено ---")
