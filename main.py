from playwright.sync_api import sync_playwright
import time
import os
from itertools import cycle
from concurrent.futures import ThreadPoolExecutor

#Altere esse valor para configurar um mínimo de vezes que vai enviar
#Cada imagem, nome, organização ou email vai ser enviado pelo menos uma vez
minimo_envios = 1000

# Altere o número abaixo para mudar a quantidade de abas feitas em paralelo(ao mesmo tempo)
# Se o seu computador não for muito bom, recomendo não alterar esse número
workers = 5

# Leitura dos arquivos
with open("nomes.txt") as f:
    nomes = [linha.strip() for linha in f.readlines()]
with open("emails.txt") as f:
    emails = [linha.strip() for linha in f.readlines()]
with open("orgs.txt") as f:
    orgs = [linha.strip() for linha in f.readlines()]
files = os.listdir("images")

max_len = max(minimo_envios, len(nomes), len(emails), len(orgs),len(files))
def repetir_para_tamanho(lista, tamanho):
    return list(item for item, _ in zip(cycle(lista), range(tamanho)))

nomes = repetir_para_tamanho(nomes, max_len)
emails = repetir_para_tamanho(emails, max_len)
orgs = repetir_para_tamanho(orgs, max_len)
files = repetir_para_tamanho(files, max_len)

def sent_forms(org, nome, email, file):
    nome = nome.split()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://comments.ustr.gov/s/submit-new-comment?docketNumber=USTR-2025-0043&fbclid=PAQ0xDSwLtzHtleHRuA2FlbQIxMQABpw_Jlis9jd9tqtKqsj7h3SJqs9BxIGdkN-HQp1jbbr2HOVZIs1RamCiuCkGw_aem_BNLl69a_1p2mSO2RioVmNg")
        
        # Espera e preenche os campos
        page.fill('input[name="Organization_Name__c"]', org)
        page.fill('input[name="First_Name__c"]', nome[0])
        page.fill('input[name="Last_Name__c"]', nome[1])
        page.fill('input[name="Email__c"]', email)
        
        page.click('button:has-text("Next")')
        time.sleep(3)

        #comment page
        page.click("button[name='Text_Value__c']")

        # Aguarda a lista de opções aparecer
        page.wait_for_selector("lightning-base-combobox-item")

        # Clica na opção desejada (por texto visível)
        page.click("lightning-base-combobox-item >> text=Unfair, Preferential Tariffs")
        page.click('button:has-text("Next")')
        time.sleep(3)

        #attachments

        page.click("button[name='fileSensitivity']")
        page.wait_for_selector("lightning-base-combobox-item")
        page.click("lightning-base-combobox-item >> text=Public Document")

        #upload de arquivo
        input_file = page.locator('input[name="fileUploader"]')
        input_file.set_input_files("./images/"+ file)

        page.wait_for_function(
            """() => {
                const el = document.querySelector('[role="progressbar"]');
                return el && el.getAttribute('aria-valuenow') === '100';
            }""",
            timeout=10000  # aguarda até 10 segundos
        )
        page.click('button:has-text("Done")')

        page.click("button[name='Text_Value__c']")
        page.wait_for_selector("lightning-base-combobox-item")
        page.click("lightning-base-combobox-item >> text=No")
        #To-DO fazer com o yes

        page.click('button:has-text("Next")')
        time.sleep(3)
        page.click('button:has-text("Submit")')

        time.sleep(1)
        browser.close()


with ThreadPoolExecutor(max_workers=workers) as executor:  # Pode ajustar o número de workers
    tarefas = [executor.submit(sent_forms, org, nome, email, file ) for org,nome,email,file in zip(orgs,nomes,emails,files)]