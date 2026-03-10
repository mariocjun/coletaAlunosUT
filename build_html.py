import json

def build_html():
    with open('vestibulares.json', 'r', encoding='utf-8') as f:
        editions = json.load(f)

    html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lista de Aprovados - Vestibulares UTFPR</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #ffcc00; /* UTFPR yellow-ish */
            background-color: #333; /* Dark background to contrast */
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .edition-card {
            background-color: #fff;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .edition-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        .edition-header h2 {
            margin: 0;
            color: #0056b3;
        }
        .edition-link {
            text-decoration: none;
            color: #fff;
            background-color: #0056b3;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        .edition-link:hover {
            background-color: #004494;
        }
        .approved-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .approved-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 4px;
            border-left: 4px solid #ddd;
            transition: border-color 0.3s;
        }
        .approved-item.checked {
            border-left-color: #28a745;
            background-color: #eafbee;
        }
        .approved-item input[type="checkbox"] {
            margin-right: 15px;
            transform: scale(1.5);
            cursor: pointer;
        }
        .approved-item a {
            text-decoration: none;
            color: #333;
            font-weight: bold;
            flex-grow: 1;
        }
        .approved-item a:hover {
            color: #0056b3;
            text-decoration: underline;
        }
        .no-links {
            color: #888;
            font-style: italic;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>Vestibulares e Sisu UTFPR - Aprovados</h1>
"""

    for ed in editions:
        html += f"""
    <div class="edition-card">
        <div class="edition-header">
            <h2>{ed['name'] if 'Sisu' in ed['name'] else 'Vestibular ' + ed['name']}</h2>
            <a href="{ed['url']}" target="_blank" class="edition-link">Ver Resultados Oficiais</a>
        </div>
        """

        if not ed['approved_links']:
            html += '<p class="no-links">Nenhum link de lista de aprovados encontrado (ou ainda não divulgado).</p>'
        else:
            html += '<ul class="approved-list">'
            for i, link in enumerate(ed['approved_links']):
                # Create a unique ID for the checkbox based on edition name and link index
                checkbox_id = f"chk-{ed['name'].replace('/', '-')}-{i}"

                # Title casing
                title = link['title']
                if 'relação nominal' in title.lower():
                    title = 'Relação Nominal dos Aprovados'
                elif title.islower():
                    title = title.title()

                html += f"""
            <li class="approved-item" id="item-{checkbox_id}">
                <input type="checkbox" id="{checkbox_id}" class="approved-checkbox" data-item-id="item-{checkbox_id}">
                <a href="{link['url']}" target="_blank">{title}</a>
            </li>"""
            html += '</ul>'

        html += """
    </div>"""

    html += """
</div>

<script>
    document.addEventListener('DOMContentLoaded', () => {
        const checkboxes = document.querySelectorAll('.approved-checkbox');

        // Load saved state
        checkboxes.forEach(checkbox => {
            const isChecked = localStorage.getItem(checkbox.id) === 'true';
            checkbox.checked = isChecked;
            updateItemStyle(checkbox);

            // Add change listener
            checkbox.addEventListener('change', (e) => {
                localStorage.setItem(checkbox.id, e.target.checked);
                updateItemStyle(e.target);
            });
        });

        function updateItemStyle(checkbox) {
            const itemId = checkbox.getAttribute('data-item-id');
            const itemElement = document.getElementById(itemId);
            if (checkbox.checked) {
                itemElement.classList.add('checked');
            } else {
                itemElement.classList.remove('checked');
            }
        }
    });
</script>

</body>
</html>
"""

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Generated index.html successfully.")

if __name__ == "__main__":
    build_html()
