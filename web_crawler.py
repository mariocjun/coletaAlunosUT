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

def get_sisu_links():
    import requests
    from bs4 import BeautifulSoup
    import urllib.parse
    import time

    base_url = 'https://www.utfpr.edu.br'

    # We will gather editions and their links from Sisu Convocados
    # The structure is: /cursos/estudenautfpr/sisu/convocados/CAMPUS/edicoes-anteriores/ANO-SEMESTRE/PDFs

    # We will organize Sisu data by Edition just like Vestibulares.
    # Edition Name (e.g., "Sisu 2021/1") -> List of Campus/Call links

    sisu_editions_dict = {} # Key: "2021/1", Value: list of approved_links dicts

    res = requests.get('https://www.utfpr.edu.br/cursos/estudenautfpr/sisu/convocados')
    if res.status_code != 200:
        return []

    soup = BeautifulSoup(res.text, 'html.parser')

    campus_links = []
    # Collect campuses
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if '/sisu/convocados/' in href and href != '/cursos/estudenautfpr/sisu/convocados':
            # Avoid the main link, get campus links
            # The last part of href is the campus, e.g., 'apucarana'
            campus = href.rstrip('/').split('/')[-1]
            if campus not in ['edicoes-anteriores', 'convocados']:
                campus_links.append((campus, urllib.parse.urljoin(base_url, href)))

    # Let's uniquely filter campus links
    campus_links = list({c[0]: c for c in campus_links}.values())

    for campus, url in campus_links:
        print(f"Scraping Sisu Convocados: {campus}")
        try:
            # 1. Look for current editions on the campus root page
            c_res = requests.get(url)
            c_soup = BeautifulSoup(c_res.text, 'html.parser')

            for a in c_soup.find_all('a'):
                href = a.get('href', '')
                text = a.text.strip()
                # If it's a direct PDF to a call
                if href.endswith('.pdf') or '@@download' in href or '@@display-file' in href:
                    # Try to infer edition from text or URL
                    # e.g., "Relação dos convocados na 1ª chamada 2024/1"
                    import re
                    match = re.search(r'(20\d{2})[-/]([12])', text + ' ' + href)
                    if match:
                        ed = f"{match.group(1)}/{match.group(2)}"
                        if ed not in sisu_editions_dict:
                            sisu_editions_dict[ed] = []
                        sisu_editions_dict[ed].append({'title': f"{campus.title()} - {text}", 'url': urllib.parse.urljoin(url, href)})

            # 2. Look into edicoes-anteriores
            ea_url = urllib.parse.urljoin(url, 'edicoes-anteriores') if url.endswith('/') else urllib.parse.urljoin(url + '/', 'edicoes-anteriores')
            ea_res = requests.get(ea_url)
            if ea_res.status_code == 200:
                ea_soup = BeautifulSoup(ea_res.text, 'html.parser')

                # Each link should be an edition
                for a in ea_soup.find_all('a'):
                    ea_href = a.get('href', '')
                    ea_text = a.text.strip()

                    import re
                    match = re.match(r'^20\d{2}[-/][12]$', ea_text)
                    if match and 'edicoes-anteriores' in ea_href:
                        ed_name = match.group(0).replace('-', '/')
                        ed_url = urllib.parse.urljoin(ea_url, ea_href)

                        # Now scrape this edition page for the PDFs
                        # print(f"  Scraping {campus} - {ed_name}")
                        pdf_res = requests.get(ed_url)
                        if pdf_res.status_code == 200:
                            pdf_soup = BeautifulSoup(pdf_res.text, 'html.parser')
                            for p_a in pdf_soup.find_all('a'):
                                p_href = p_a.get('href', '')
                                p_text = p_a.text.strip()

                                # Sometimes links are just normal relative links ending in .pdf
                                if p_href.endswith('.pdf') or '@@download' in p_href or '@@display-file' in p_href:
                                    if ed_name not in sisu_editions_dict:
                                        sisu_editions_dict[ed_name] = []

                                    full_p_url = urllib.parse.urljoin(ed_url, p_href)
                                    # Avoid duplicates
                                    if not any(l['url'] == full_p_url for l in sisu_editions_dict[ed_name]):
                                        sisu_editions_dict[ed_name].append({'title': f"{campus.title()} - {p_text}", 'url': full_p_url})

        except Exception as e:
            print(f"Error scraping {campus}: {e}")

    # Convert dictionary back to the list structure we use
    new_editions = []
    for ed_name, links in sisu_editions_dict.items():
        if links:
            new_editions.append({
                'name': f"Sisu {ed_name}",
                'url': 'https://www.utfpr.edu.br/cursos/estudenautfpr/sisu/convocados', # generic root url
                'approved_links': links
            })

    # Sort them by name descending
    new_editions.sort(key=lambda x: x['name'], reverse=True)
    return new_editions

def merge_and_save():
    import json

    # Load existing vestibulares
    with open('vestibulares.json', 'r', encoding='utf-8') as f:
        vestibulares = json.load(f)

    sisu_data = get_sisu_links()

    # Add Sisu data to the end
    all_data = vestibulares + sisu_data

    with open('vestibulares.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print("Merged Vestibular and Sisu data saved to vestibulares.json")

if __name__ == '__main__':
    # Only run the merge for now to avoid re-scraping vestibulares unnecessarily
    merge_and_save()
