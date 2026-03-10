import requests
from bs4 import BeautifulSoup
import urllib.parse
import json

base_url = 'https://www.utfpr.edu.br'

def get_editions():
    editions = []

    # 1. Fetch current edition
    res = requests.get('https://www.utfpr.edu.br/cursos/estudenautfpr/vestibular')
    soup = BeautifulSoup(res.text, 'html.parser')
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if '/vestibular/edicoes/' in href and '/resultados' in href:
            parts = href.split('/')
            try:
                ed_idx = parts.index('edicoes')
                year_sem = parts[ed_idx+1]
                ed_name = year_sem.replace('-', '/')
                url = urllib.parse.urljoin(base_url, href)
                if not any(e['name'] == ed_name for e in editions):
                    editions.append({'name': ed_name, 'url': url, 'approved_links': []})
            except ValueError:
                pass

    # 2. Fetch previous editions
    res = requests.get('https://www.utfpr.edu.br/cursos/estudenautfpr/vestibular/edicoes-anteriores')
    soup = BeautifulSoup(res.text, 'html.parser')
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if href and '/vestibular/edicoes/' in href:
            text = link.text.strip()
            if text:
                ed_name = text

                # Check for direct results link
                results_link = urllib.parse.urljoin(base_url, href)
                if not results_link.endswith('/'):
                    results_link += '/'
                results_link += 'resultados'

                res_ed = requests.get(urllib.parse.urljoin(base_url, href))
                soup_ed = BeautifulSoup(res_ed.text, 'html.parser')
                for a in soup_ed.find_all('a'):
                    a_href = a.get('href', '')
                    if 'resultados' in a_href.lower():
                        results_link = urllib.parse.urljoin(base_url, a_href)
                        break

                if not any(e['name'] == ed_name for e in editions):
                    editions.append({'name': ed_name, 'url': results_link, 'approved_links': []})

    return editions

def get_aprovados_links(ed):
    url = ed['url']
    try:
        res = requests.get(url)
        if res.status_code != 200:
            return
        soup = BeautifulSoup(res.text, 'html.parser')

        # Look for PDF links first
        for link in soup.find_all('a'):
            text = link.text.strip().lower()
            href = link.get('href', '')
            if ('aprovados' in text or 'primeira chamada' in text or '1ª chamada' in text):
                full_url = urllib.parse.urljoin(url, href)

                if full_url.endswith('.pdf') or '@@display-file' in full_url:
                    if full_url not in [l['url'] for l in ed['approved_links']]:
                        ed['approved_links'].append({'title': text, 'url': full_url})
                elif 'primeira-chamada' in full_url.lower():
                    # Navigate inside to find campus links
                    res_pc = requests.get(full_url)
                    if res_pc.status_code == 200:
                        soup_pc = BeautifulSoup(res_pc.text, 'html.parser')
                        for pc_link in soup_pc.find_all('a'):
                            pc_href = pc_link.get('href', '')
                            pc_text = pc_link.text.strip()
                            if '/resultados/chamadas/' in pc_href or 'aprovados' in pc_href.lower():
                                pc_full_url = urllib.parse.urljoin(full_url, pc_href)
                                if pc_full_url not in [l['url'] for l in ed['approved_links']]:
                                    ed['approved_links'].append({'title': pc_text, 'url': pc_full_url})

        # Sometimes campuses are listed directly on the results page (like 2025/1)
        if not ed['approved_links']:
            for link in soup.find_all('a'):
                href = link.get('href', '')
                text = link.text.strip()
                if '/resultados/' in href and not href.endswith('/resultados'):
                    # Check if it looks like a campus link
                    campuses = ['apucarana', 'campo-mourao', 'cornelio-procopio', 'curitiba', 'dois-vizinhos',
                                'francisco-beltrao', 'guarapuava', 'londrina', 'medianeira', 'pato-branco',
                                'ponta-grossa', 'santa-helena', 'toledo']
                    if any(c in href for c in campuses):
                        full_url = urllib.parse.urljoin(url, href)
                        if full_url not in [l['url'] for l in ed['approved_links']]:
                            ed['approved_links'].append({'title': text, 'url': full_url})

    except Exception as e:
        print(f"Error for {url}: {e}")

editions = get_editions()
for ed in editions:
    get_aprovados_links(ed)

with open('vestibulares.json', 'w', encoding='utf-8') as f:
    json.dump(editions, f, ensure_ascii=False, indent=4)
print("Saved to vestibulares.json")
