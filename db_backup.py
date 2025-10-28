import requests
from bs4 import BeautifulSoup
import re
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class DBExecute:
    def DBExecute():
        # ## like fap no hfox
        # Lista de User-Agents
        user_agents = [
          "Mozilla/5.0 (Linux; Android 13; SM-G780G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
          "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        ]
        
        def get_csrf_token(session, url, headers):
          """Obtém o token CSRF da página da galeria"""
          tentativa = 0
          while True:
              try:
                  response = session.get(url, headers=headers, timeout=10)
                  response.raise_for_status()
                  soup = BeautifulSoup(response.text, 'html.parser')
        
                  csrf_token = soup.find('meta', attrs={'name': 'csrf-token'})
                  if csrf_token:
                      return csrf_token.get('content')
        
                  csrf_input = soup.find('input', attrs={'name': '_token'})
                  if csrf_input:
                      return csrf_input.get('value')
        
                  js_match = re.search(r'csrf[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']', response.text, re.IGNORECASE)
                  if js_match:
                      return js_match.group(1)
        
                  print(f"AVISO: Token CSRF não encontrado para {url}")
                  if tentativa <= 6:
                      tentativa += 1
                  else:
                      return None
              except requests.exceptions.RequestException as e:
                  print(f"Erro ao obter CSRF token para {url}: {e}")
                  print(f"Tentativa {tentativa + 1}")
                  tentativa += 1
                  if tentativa > 6:
                      return None
        
        def fetch_gallery_ids(artist, page=None):
          """Coletar IDs de galerias de uma página específica"""
          gallery_ids = set()
          base_url = f"https://hentaifox.com/artist/{artist}/"
          url = base_url if page is None else f"{base_url}pag/{page}/"
        
          headers = {
              "accept-language": "pt-BR,pt;q=0.9",
              "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
              "sec-fetch-dest": "document",
              "sec-fetch-mode": "navigate",
              "sec-fetch-site": "same-origin",
              "User-Agent": random.choice(user_agents)
          }
        
          print(f"Coletando IDs da página: {url}")
          try:
              session = requests.Session()
              response = session.get(url, headers=headers, timeout=10)
              if response.status_code == 404:
                  print(f"Página {url} não encontrada (404).")
                  return gallery_ids
              response.raise_for_status()
              soup = BeautifulSoup(response.text, 'html.parser')
        
              for link in soup.find_all('a', href=True):
                  href = link['href']
                  match = re.search(r'/gallery/(\d+)/', href)
                  if match:
                      gallery_ids.add(int(match.group(1)))
                      print(f"ID encontrado: {match.group(1)}")
        
              return gallery_ids
          except requests.exceptions.RequestException as e:
              print(f"Erro ao acessar {url}: {e}")
              return gallery_ids
        
        def get_gallery_ids(artist, max_pages=10, threads_per_batch=3):
          """Coletar IDs de todas as páginas do artista usando threading"""
          gallery_ids = set()
          pages = [None] + list(range(2, max_pages + 1))
        
          for batch in range(0, len(pages), threads_per_batch):
              batch_pages = pages[batch:batch + threads_per_batch]
              print(f"\nProcessando lote de páginas: {batch_pages}")
        
              with ThreadPoolExecutor(max_workers=threads_per_batch) as executor:
                  future_to_page = {executor.submit(fetch_gallery_ids, artist, page): page for page in batch_pages}
                  for future in as_completed(future_to_page):
                      page = future_to_page[future]
                      try:
                          ids = future.result()
                          gallery_ids.update(ids)
                      except Exception as e:
                          print(f"Erro no processamento da página {page}: {e}")
        
              time.sleep(random.uniform(1, 3))
        
          return list(gallery_ids)
        
        def like_single_gallery(gallery_id):
          """Dá like e fap em uma única galeria, simulando atualização da página entre ações"""
          url_like = "https://hentaifox.com/includes/add_like.php"
          url_fap = "https://hentaifox.com/includes/add_fap.php"
          url_gallery = f"https://hentaifox.com/gallery/{gallery_id}/"
          session = requests.Session()
          user_agent = random.choice(user_agents)
        
          headers = {
              "accept-language": "pt-BR,pt;q=0.9",
              "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
              "sec-ch-ua-mobile": "?1",
              "sec-ch-ua-platform": '"Android"',
              "User-Agent": user_agent,
              "referer": url_gallery
          }
        
          # Headers para GET
          headers_get = headers.copy()
          headers_get.update({
              "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
              "sec-fetch-dest": "document",
              "sec-fetch-mode": "navigate",
              "sec-fetch-site": "same-origin"
          })
        
          # Passo 1: Obter token CSRF para like
          csrf_token = get_csrf_token(session, url_gallery, headers_get)
          if not csrf_token:
              print(f"Falha ao obter CSRF token para like na galeria {gallery_id}. Pulando.")
              return False
        
          print(f"Token CSRF para like na galeria {gallery_id}: {csrf_token[:20]}...")
        
          # Headers para POST (like e fap)
          headers_post = headers.copy()
          headers_post.update({
              "accept": "*/*",
              "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
              "sec-fetch-dest": "empty",
              "sec-fetch-mode": "cors",
              "sec-fetch-site": "same-origin",
              "x-requested-with": "XMLHttpRequest",
              "x-csrf-token": csrf_token,
              "priority": "u=1, i"  # Adicionado para fap, conforme o fetch
          })
        
          # Dados para ambas as requisições
          data = {"gallery_id": str(gallery_id)}
        
          # Enviar like
          try:
              response = session.post(url_like, headers=headers_post, data=data, timeout=10)
              print(f"Galeria {gallery_id} - Like Status: {response.status_code}")
              print(f"Galeria {gallery_id} - Like Resposta: {response.text.strip()}")
        
              if "success" in response.text.lower():
                  print(f"Like enviado com sucesso para galeria {gallery_id}!")
              elif "already" in response.text.lower():
                  print(f"Erro: Like já registrado para galeria {gallery_id}.")
              else:
                  print(f"Erro desconhecido no like para galeria {gallery_id}. Resposta: {response.text}")
                  return False
          except requests.exceptions.RequestException as e:
              print(f"Erro na solicitação de like para galeria {gallery_id}: {e}")
              return False
              
        def fap_single_gallery(gallery_id):
          """Dá like e fap em uma única galeria, simulando atualização da página entre ações"""
          url_like = "https://hentaifox.com/includes/add_like.php"
          url_fap = "https://hentaifox.com/includes/add_fap.php"
          url_gallery = f"https://hentaifox.com/gallery/{gallery_id}/"
          session = requests.Session()
          user_agent = random.choice(user_agents)
        
          headers = {
              "accept-language": "pt-BR,pt;q=0.9",
              "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
              "sec-ch-ua-mobile": "?1",
              "sec-ch-ua-platform": '"Android"',
              "User-Agent": user_agent,
              "referer": url_gallery
          }
        
          # Headers para GET
          headers_get = headers.copy()
          headers_get.update({
              "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
              "sec-fetch-dest": "document",
              "sec-fetch-mode": "navigate",
              "sec-fetch-site": "same-origin"
          })
                
          # Passo 2: Simular atualização da página (novo GET)
          time.sleep(random.uniform(0.5, 1.5))  # Pequeno delay para simular navegação
          csrf_token = get_csrf_token(session, url_gallery, headers_get)
          if not csrf_token:
              print(f"Falha ao obter CSRF token para fap na galeria {gallery_id}. Pulando.")
              return False
        
          print(f"Token CSRF para fap na galeria {gallery_id}: {csrf_token[:20]}...")
        
          # Atualizar token CSRF nos headers para fap
          headers_post["x-csrf-token"] = csrf_token
        
          # Passo 3: Enviar fap
          try:
              response = session.post(url_fap, headers=headers_post, data=data, timeout=10)
              print(f"Galeria {gallery_id} - Fap Status: {response.status_code}")
              print(f"Galeria {gallery_id} - Fap Resposta: {response.text.strip()}")
        
              if "success" in response.text.lower():
                  print(f"Fap enviado com sucesso para galeria {gallery_id}!")
                  return True
              elif "already" in response.text.lower():
                  print(f"Erro: Fap já registrado para galeria {gallery_id}.")
                  return False
              else:
                  print(f"Erro desconhecido no fap para galeria {gallery_id}. Resposta: {response.text}")
                  return False
          except requests.exceptions.RequestException as e:
              print(f"Erro na solicitação de fap para galeria {gallery_id}: {e}")
              return False
        
        def like_and_fap_galleries(gallery_ids, gallery_ids_fp, max_concurrent=50):
          """Dá like e fap em galerias em lotes de até max_concurrent usando threading"""
          for batch in range(0, len(gallery_ids_fp), max_concurrent):
              batch_ids = gallery_ids_fp[batch:batch + max_concurrent]
              print(f"\nProcessando lote de {len(batch_ids)} galerias: {batch_ids}")
        
              with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                  future_to_id = {executor.submit(fap_single_gallery, gallery_id): gallery_id for gallery_id in batch_ids}
                  for future in as_completed(future_to_id):
                      gallery_id = future_to_id[future]
                      try:
                          future.result()
                      except Exception as e:
                          print(f"Erro no processamento da galeria {gallery_id}: {e}")

          for batch in range(0, len(gallery_ids), max_concurrent):
              batch_ids = gallery_ids[batch:batch + max_concurrent]
              print(f"\nProcessando lote de {len(batch_ids)} galerias: {batch_ids}")
        
              with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                  future_to_id = {executor.submit(like_single_gallery, gallery_id): gallery_id for gallery_id in batch_ids}
                  for future in as_completed(future_to_id):
                      gallery_id = future_to_id[future]
                      try:
                          future.result()
                      except Exception as e:
                          print(f"Erro no processamento da galeria {gallery_id}: {e}")
                          
              # time.sleep(random.uniform(2, 5))
        
        # Definir artista e executar
        artist = "kuroinu-juu"
        # print(f"\nIniciando coleta de IDs para artista: {artist}")
        # gallery_ids = get_gallery_ids(artist, max_pages=8, threads_per_batch=8)
        # print(f"\nVetor de IDs de galerias coletado: {gallery_ids}")
        # print(f"Total de galerias encontradas: {len(gallery_ids)}")
        # like_and_fap_galleries(gallery_ids, max_concurrent=60)
        gallery_ids = [94975,48099,2814,115811,133693,100489,121865,69316,34208,48359]
        gallery_ids_fp = [64963,51950,25621,23527,20141,14909,11454,10181,6988,52636]
        
        # gallery_ids = [1792, 145411, 3846, 80392, 121865, 5384, 11277, 42510, 38164, 25621, 42519, 16924, 147741, 63262, 32285, 12061, 5158, 36393, 10794, 2858, 133420, 23597, 63535, 47920, 23855, 47, 2096, 48182, 112183, 12856, 57, 5434, 18747, 58, 133693, 14909, 59, 60, 825, 61, 61763, 62, 30277, 11846, 21830, 83528, 34633, 47946, 32074, 6988, 28233, 67921, 13137, 10836, 150104, 82008, 23128, 2907, 101212, 42589, 115811, 36965, 62822, 62566, 42092, 55405, 4719, 51570, 20850, 3707, 54913, 4739, 646, 4743, 5000, 100489, 4744, 7822, 10126, 7570, 4754, 10898, 18066, 108438, 46742, 25491, 30362, 922, 52636, 9885, 40094, 51615, 34208, 20131, 3748, 10149, 10151, 5800, 4779, 18860, 16045, 20141, 2482, 54963, 40887, 5562, 5563, 11454, 4799, 64963, 69316, 17093, 16070, 10181, 25544, 126154, 129743, 129744, 31697, 2260, 33238, 51160, 49882, 31451, 39132, 6109, 29403, 7903, 33248, 2016, 12770, 69603, 48099, 6374, 48359, 23527, 125165, 51950, 7151, 1520, 1008, 1007, 68599, 2814, 94975]
        like_and_fap_galleries(gallery_ids, gallery_ids_fp, max_concurrent=60)
