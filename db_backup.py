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
    def execute2():    
        import requests
        import concurrent.futures
        import time
        import random
        import json
        
        # --- CONFIGURAÇÕES DO SCRIPT ---
        # 1. Defina o número TOTAL de requisições que você quer enviar
        TOTAL_REQUESTS = 50000 #entre 1000 e 7000
        MULTIPLIER = 50
        EXTRA_UP = ['21730','3372','10602','2705','3032','34689','14126','10614','2169','2184','2815','4195','10507','2630','2058','3252','4061','4757','3799','49826','41278','45432','53149','2004']
        EXTRA_UP2 = ['21730','3372','10602','2705','34689','2169','10614','8988','2815','3799','4195','3252','49826','41278','45432','53149','2004','68870','11611','3032']
        EXTRA_UP3 = ['21730','3372','10602','2705','34689','10614','49826','68870','45432','14548','21990','45050','38779','2169','8988','49826','11611','38779','27016','3032']
        EXTRA_PLUS = ['3372','10602','2705','14548','2815','2169','3649','5589','3032','49826','8988','10614','34689']
        EXTRA_ULTRA = ['3372','10602','3032','3649','8988','2169','2815','10614','34689','2705','49826']
        # EXTRA_PLUS_ULTRA = ['14548','2815','2169','3649','5589']
        
        # 2. Defina quantas requisições devem ser executadas SIMULTANEAMENTE (threads)
        NUM_THREADS = 250
        # 3041tower_of_gray
        # 2905yellow_temperance
        # 3662scary_monsters
        # 10614 shidare_zakura
        # 48973 hypnotism_is_just_make_believe
        # 3648 aqua_necklace
        # 3685 burning_down_the_house
        # 3654 in_a_silent_way
        ALVOS = [
            # bai asuka
            {'mid': '18828', 'vote': 'up', 'slug': 'hametorare'},
            {'mid': '28137', 'vote': 'up', 'slug': 'mating_with_mother'},
            {'mid': '39823', 'vote': 'up', 'slug': 'shokurei'},
            {'mid': '49274', 'vote': 'up', 'slug': 'my_mother_is_my_friends_slave'},
            {'mid': '20439', 'vote': 'up', 'slug': 'impregnated_mother'},
            # BOSSHI
            {'mid': '2705', 'vote': 'up', 'slug': 'ojousama_wa_h_ga_osuki'},
            # MANABE JOUJI
            {'mid': '2266', 'vote': 'up', 'slug': 'ring_x_mama'},
            {'mid': '2608', 'vote': 'up', 'slug': 'koisuru_ushichichi'},
            # ZUCCHINI
            {'mid': '6059', 'vote': 'up', 'slug': 'incest_manual'},
            # REDROP
            {'mid': '63463', 'vote': 'up', 'slug': 'princess_plap'},
            {'mid': '4417', 'vote': 'up', 'slug': 'henkano_redrop'},
            # KON KIT
            {'mid': '3372', 'vote': 'up', 'slug': 'honey_dip_kon_kit'},
            {'mid': '25892', 'vote': 'up', 'slug': 'kaya_netori_kayanee_series'},
            {'mid': '10602', 'vote': 'up', 'slug': 'involuntary_but_consensual_sex'},
            {'mid': '46970', 'vote': 'up', 'slug': 'chaos_comics'},
            {'mid': '65662', 'vote': 'up', 'slug': 'lower_your_guard_get_fucked'},
            {'mid': '2008', 'vote': 'up', 'slug': 'bitch_trap'},
            {'mid': '20951', 'vote': 'up', 'slug': 'yoridori_bitch'},
            {'mid': '21274', 'vote': 'up', 'slug': 'yurushite_anata'},
            {'mid': '38237', 'vote': 'up', 'slug': 'sonna_riyuu_de_yararechau'},
            {'mid': '10598', 'vote': 'up', 'slug': 'netorare_new_heroine'},
            # random
            {'mid': '21730', 'vote': 'up', 'slug': 'greece_crysis'},
            # 
            {'mid': '27016', 'vote': 'up', 'slug': 'tales_of_harem_in_another_world'},
            # {'mid': '5736', 'vote': 'up', 'slug': 'nangoku_harem'},
            # {'mid': '4099', 'vote': 'up', 'slug': 'doa_harem'},
            # {'mid': '10769', 'vote': 'up', 'slug': 'harem_variety_pack'},
            # {'mid': '18483', 'vote': 'up', 'slug': 'p5_harem'},
            # {'mid': '18222', 'vote': 'up', 'slug': 'fudeoro_sisters'},
            # {'mid': '11611', 'vote': 'up', 'slug': 'i_am_everyones_landlord'},
            # {'mid': '68870', 'vote': 'up', 'slug': 'i_cant_get_it_up_without_two_pairs_of_big_breasts'},
            # {'mid': '6777', 'vote': 'up', 'slug': 'regrettable_heroines'},
            # {'mid': '50438', 'vote': 'up', 'slug': 'sudden_harem_life_after'},
            # {'mid': '21974', 'vote': 'up', 'slug': 'yukemuri_harem_monogatari'},
            # {'mid': '44329', 'vote': 'up', 'slug': 'nanakas_paradise'},
            
            # {'mid': '45432', 'vote': 'up', 'slug': 'elf_ni_inmon_o_tsukeru_hon'},
            # {'mid': '21154', 'vote': 'up', 'slug': 'makipet'},
            # {'mid': '22575', 'vote': 'up', 'slug': 'dangan_archive'},
            # {'mid': '20203', 'vote': 'up', 'slug': 'shoujo_kaishun'},
            # {'mid': '26338', 'vote': 'up', 'slug': 'bibi_collection'},
            
            # {'mid': '53149', 'vote': 'up', 'slug': 'hahaue_mo_mesu_orc'},
            # {'mid': '2004', 'vote': 'up', 'slug': 'blue_eyes'},
            {'mid': '14548', 'vote': 'up', 'slug': 'an_elder_sister'},
            # {'mid': '21432', 'vote': 'up', 'slug': 'ane_naru_mono'},
            # kimi_wa_akogare_no_tawawa
            # {'mid': '45050', 'vote': 'up', 'slug': 'sono_bisque_doll_wa_h_o_suru'},
            # {'mid': '34594', 'vote': 'up', 'slug': 'rental_kanojo_osawari_shimasu'},
            # {'mid': '3883', 'vote': 'up', 'slug': 'lovematio'},
            # {'mid': '18482', 'vote': 'up', 'slug': 'sleeping_sister'},
            # {'mid': '58872', 'vote': 'up', 'slug': 'kimi_wa_akogare_no_tawawa'},
            
            ##{'mid': '21990', 'vote': 'up', 'slug': 'bullied_revenge_hypnosis'},
            ##{'mid': '38779', 'vote': 'up', 'slug': 'family_control'},
            # {'mid': '17542', 'vote': 'up', 'slug': 'hypnosis_sex_guidance'},
            # {'mid': '31449', 'vote': 'up', 'slug': 'dakuon'},
            
            # {'mid': '2572', 'vote': 'up', 'slug': 'pink_cherry_pie'},
            # {'mid': '6731', 'vote': 'up', 'slug': 'mon_mon_animal_girl'},
            # {'mid': '2431', 'vote': 'up', 'slug': 'momozono_gakuen'},
            # {'mid': '4422', 'vote': 'up', 'slug': 'purupuru_milk_feeling'},
            # {'mid': '31449', 'vote': 'up', 'slug': 'rental_kanojo_osawari_shimasu'},
            {'mid': '49826', 'vote': 'up', 'slug': 'my_little_sisters_are_slutty_orcs'},
            # {'mid': '41278', 'vote': 'up', 'slug': 'horny_isekai_elfs_evil_eye'},
            # {'mid': '45432', 'vote': 'up', 'slug': 'elf_ni_inmon_o_tsukeru_hon'},
            # {'mid': '53149', 'vote': 'up', 'slug': 'hahaue_mo_mesu_orc'},
            # {'mid': '2004', 'vote': 'up', 'slug': 'blue_eyes'},
            
            {'mid': '8988', 'vote': 'up', 'slug': 'made_in_heaven_jupiter'},
            # {'mid': '3675', 'vote': 'up', 'slug': 'tubala_bells'},
            # {'mid': '3498', 'vote': 'up', 'slug': 'sex_pistols'},
            {'mid': '3032', 'vote': 'up', 'slug': 'pearl_jam'},
            {'mid': '3649', 'vote': 'up', 'slug': 'beach_boy'},
            # {'mid': '3596', 'vote': 'up', 'slug': 'welcome_to_tokoharusou'},
            # {'mid': '3662', 'vote': 'up', 'slug': 'scary_monsters'},
            # {'mid': '2905', 'vote': 'up', 'slug': 'yellow_temperance'},
            # {'mid': '3041', 'vote': 'up', 'slug': 'tower_of_gray'},
            {'mid': '10614', 'vote': 'up', 'slug': 'shidare_zakura'},
            # {'mid': '48973', 'vote': 'up', 'slug': 'hypnotism_is_just_make_believe'},
            # {'mid': '3648', 'vote': 'up', 'slug': 'aqua_necklace'},
            # {'mid': '3685', 'vote': 'up', 'slug': 'burning_down_the_house'},
            # {'mid': '3654', 'vote': 'up', 'slug': 'in_a_silent_way'},
            # {'mid': '26602', 'vote': 'up', 'slug': 'love_triangle_z'},#ano_hi_no_tegomesan
            # {'mid': '13486', 'vote': 'up', 'slug': 'ano_hi_no_tegomesan'},
            # {'mid': '7639', 'vote': 'up', 'slug': 'another_one_bite_the_dust'},
            # {'mid': '3650', 'vote': 'up', 'slug': 'cream_starter'},
            # {'mid': '33288', 'vote': 'up', 'slug': 'flirtation_sped_forward'},
            # {'mid': '13234', 'vote': 'up', 'slug': 'game_of_lust'},
            # {'mid': '2718', 'vote': 'up', 'slug': 'sailor_moon_gold_experience'},
            # {'mid': '3486', 'vote': 'up', 'slug': 'hierophant_green'},
            # {'mid': '63520', 'vote': 'up', 'slug': 'just_for_tonight_ill_be_your_bitch'},
            # {'mid': '19443', 'vote': 'down', 'slug': 'kayoubi_no_yurameki'},
            # {'mid': '14074', 'vote': 'down', 'slug': 'magicians_red'},
            # {'mid': '3655', 'vote': 'up', 'slug': 'killer_queen'},
            # {'mid': '3017', 'vote': 'up', 'slug': 'diver_down'},
            # {'mid': '40339', 'vote': 'up', 'slug': 'oasis_kuroinu_juu'},
            # {'mid': '22442', 'vote': 'up', 'slug': 'ojisan_to_futarikiri'},
            # {'mid': '3722', 'vote': 'down', 'slug': 'red_hot_chili_peppers'},
            # {'mid': '3036', 'vote': 'up', 'slug': 'sheer_heart_attack'},
            # {'mid': '3665', 'vote': 'up', 'slug': 'sky_high'},
            # {'mid': '5589', 'vote': 'up', 'slug': 'soft_and_wet'},
            # {'mid': '8040', 'vote': 'up', 'slug': 'submission_super_moon'},
            # {'mid': '3671', 'vote': 'up', 'slug': 'superfly'},
            # {'mid': '33063', 'vote': 'up', 'slug': 'tohth'},
        
            # {'mid': '2980', 'vote': 'up', 'slug': 'atum'},
            # {'mid': '16189', 'vote': 'up', 'slug': 'chocolate_disco'},
            # {'mid': '16307', 'vote': 'up', 'slug': 'fuuka_and_a_train_of_excited_molesters'},
            # {'mid': '3658', 'vote': 'up', 'slug': 'man_in_the_mirror'},
            # {'mid': '14992', 'vote': 'up', 'slug': 'earth_wind_and_fire'},
            # {'mid': '12356', 'vote': 'up', 'slug': 'planet_waves'},
            # {'mid': '21767', 'vote': 'up', 'slug': 'onegai_azumaya'},
            # {'mid': '31185', 'vote': 'up', 'slug': 'queen_of_spades'},
            # {'mid': '24414', 'vote': 'up', 'slug': 'saturday_girls_cant_hold_it_in'},
            # {'mid': '17522', 'vote': 'up', 'slug': 'soft_machine'},
            # {'mid': '6933', 'vote': 'up', 'slug': 'submission_r_re_mercury'},
            # {'mid': '3669', 'vote': 'up', 'slug': 'submission_mercury_plus'},
            # {'mid': '3667', 'vote': 'up', 'slug': 'submission_jupiter_plus'},
            # {'mid': '3670', 'vote': 'up', 'slug': 'submission_venus'},
            # {'mid': '11165', 'vote': 'up', 'slug': 'submission_saturn'},
            # {'mid': '3668', 'vote': 'up', 'slug': 'submission_mars'},
            # {'mid': '3040', 'vote': 'up', 'slug': 'the_grateful_dead'},
            # {'mid': '18878', 'vote': 'up', 'slug': 'tegomisan'},
            # {'mid': '54851', 'vote': 'up', 'slug': 'oyako_de_onsen_ni_ittara_netorare_onsen_deshita'},
            # {'mid': '22361', 'vote': 'up', 'slug': 'osawarisan'},
            # {'mid': '12407', 'vote': 'up', 'slug': 'weather_report_genshiken'},
            # {'mid': '46948', 'vote': 'up', 'slug': 'sweet_hearts_lesson'},
            {'mid': '2668', 'vote': 'up', 'slug': 'sweet_hearts_kisaragi_gunma'},
            {'mid': '2815', 'vote': 'up', 'slug': 'mai_favorite'},
            # {'mid': '2220', 'vote': 'up', 'slug': 'love_selection'},
            # {'mid': '14126', 'vote': 'up', 'slug': 'hina_project'},#
            {'mid': '2169', 'vote': 'up', 'slug': 'giri_giri_sisters'},
            # {'mid': '3753', 'vote': 'up', 'slug': 'strawberry_panic'},
            # {'mid': '3770', 'vote': 'up', 'slug': 'kozue_panic'},
            # {'mid': '3895', 'vote': 'up', 'slug': 'fukufuku_kyousei_event'},
            # {'mid': '2921', 'vote': 'up', 'slug': 'hime_otome'},
            # {'mid': '2184', 'vote': 'up', 'slug': 'honey_blonde'},
            # {'mid': '57050', 'vote': 'up', 'slug': 'as_innocent_as_a_bunny_the_pretty_guardian_loses_to_the_dick'},
            # {'mid': '58503', 'vote': 'up', 'slug': 'chin_make_makochan_with_amichan'},
            # {'mid': '55816', 'vote': 'up', 'slug': 'hotaru_no_oishasan_gokko'},
            # {'mid': '19131', 'vote': 'up', 'slug': 'ninshin_shichatta_dareka_tasukete'},
            # {'mid': '66415', 'vote': 'up', 'slug': 'mars_impregnation'},
            # {'mid': '33136', 'vote': 'up', 'slug': 'mercury_no_shojo_soushitsu_de_ippatsu_nu_kitai'},
            # {'mid': '36984', 'vote': 'up', 'slug': 'nakadashi_seishori_benki_reichan_shojo_soushitsu'},
            # {'mid': '9657', 'vote': 'up', 'slug': 'amagami_harem_root'},
            # {'mid': '7641', 'vote': 'up', 'slug': 'a_straight_line_to_love'},
            # {'mid': '3419', 'vote': 'up', 'slug': 'impossible'},
            # {'mid': '4658', 'vote': 'up', 'slug': 'momoiro_passion'},
            # {'mid': '2024', 'vote': 'up', 'slug': 'alice_in_sexland'},
            # {'mid': '2025', 'vote': 'up', 'slug': 'alice_in_sexland_extreme'},
            # {'mid': '42203', 'vote': 'up', 'slug': 'alice'},
            # {'mid': '6622', 'vote': 'up', 'slug': 'kayumidome'},
            # {'mid': '8415', 'vote': 'up', 'slug': 'secret_assignation'},
            # {'mid': '11988', 'vote': 'up', 'slug': 'sae_milk'},
            # {'mid': '2245', 'vote': 'up', 'slug': 'oh_miss_nanase'},
            # {'mid': '6483', 'vote': 'up', 'slug': 'my_neighbors_are_aliens'},
            # {'mid': '2055', 'vote': 'up', 'slug': 'maid_in_teacher'},
        
            # {'mid': '19129', 'vote': 'up', 'slug': 'milf_of_steel'},
            # {'mid': '17689', 'vote': 'up', 'slug': 'amazing_eighth_wonder'},
            # {'mid': '20876', 'vote': 'up', 'slug': 'dont_meddle_in_my_daughter'},
            # {'mid': '32975', 'vote': 'up', 'slug': 'uncanny_eighthwonder'},
            # {'mid': '17279', 'vote': 'up', 'slug': 'oyako_heroine_funtousu'},
            # {'mid': '10507', 'vote': 'up', 'slug': 'one_hurricane'},
            # {'mid': '62736', 'vote': 'up', 'slug': 'daughter_falling_into_stepfather'},
            # {'mid': '9272', 'vote': 'up', 'slug': 'the_working_goddess'},
            {'mid': '34689', 'vote': 'up', 'slug': 'icha_icha_unbalance'},
            # {'mid': '4029', 'vote': 'up', 'slug': 'kan_ni_sakura'},
            # {'mid': '4191', 'vote': 'up', 'slug': 'yuri_and_friends_full_color'},
            # {'mid': '39860', 'vote': 'up', 'slug': 'the_athena_and_friends_ninetynine'},
            # {'mid': '44020', 'vote': 'up', 'slug': 'the_yuri_and_friends_ninetysix'},
            # {'mid': '4176', 'vote': 'up', 'slug': 'hinako_max'},
            # {'mid': '4194', 'vote': 'up', 'slug': 'yuri_and_friends_mai_special'},
            # {'mid': '4195', 'vote': 'up', 'slug': 'mary_special'},
            # {'mid': '4190', 'vote': 'up', 'slug': 'yuri_and_friends'},
            # {'mid': '3560', 'vote': 'up', 'slug': 'rei_slave_to_the_grind'},
            # {'mid': '2967', 'vote': 'up', 'slug': 'a_housewifes_temptation'},
            # {'mid': '6295', 'vote': 'up', 'slug': 'i_cant_help_but_notice_the_onboard_uniforms_2199'},
            # {'mid': '3248', 'vote': 'up', 'slug': 'mio_mugi_densha_chikan'},
            # {'mid': '3097', 'vote': 'up', 'slug': 'reset_one'},
            # {'mid': '3633', 'vote': 'up', 'slug': 'tiger_dance_and_dragon'},
            # {'mid': '7923', 'vote': 'up', 'slug': 'toukiden'},
            # {'mid': '8039', 'vote': 'up', 'slug': 'st_dead_or_alive_highschool'},
            # {'mid': '5367', 'vote': 'up', 'slug': 'h.sas4'},
            # {'mid': '2630', 'vote': 'up', 'slug': 'cheerism'},
            # {'mid': '2058', 'vote': 'up', 'slug': 'milk_mama'},
            # {'mid': '3799', 'vote': 'up', 'slug': 'apron_love'},
            # {'mid': '3473', 'vote': 'up', 'slug': 'do_the_piston_until_breaking'},
            # {'mid': '4757', 'vote': 'up', 'slug': 'female_teachers'},
            # {'mid': '6163', 'vote': 'up', 'slug': 'kurikyun_5'},
            # {'mid': '2483', 'vote': 'up', 'slug': 'egoist_drill_murata'},
            # {'mid': '2049', 'vote': 'up', 'slug': 'houkago_drop'},
            # {'mid': '2043', 'vote': 'up', 'slug': 'hishoka_drop'},
            # {'mid': '2044', 'vote': 'up', 'slug': 'hishoka_drop_mix'},
            # {'mid': '45463', 'vote': 'up', 'slug': 'hajimete_no_sense'},
            # {'mid': '46999', 'vote': 'up', 'slug': 'ero_ninja_scrolls'},
            # {'mid': '2208', 'vote': 'up', 'slug': 'private_teacher'},
            # {'mid': '5179', 'vote': 'up', 'slug': 'kyonyuu_wakazuma_nakadashi_club'},
            # {'mid': '2401', 'vote': 'up', 'slug': 'inransei_souseiji'},
            # {'mid': '2398', 'vote': 'up', 'slug': 'hitozuma_lovers'},
            # {'mid': '2348', 'vote': 'up', 'slug': 'ane_plus'},
            # {'mid': '2046', 'vote': 'up', 'slug': 'horny_apartment'},
            # {'mid': '4884', 'vote': 'up', 'slug': 'my_creampie_diary'},
            # {'mid': '6900', 'vote': 'up', 'slug': 'kokuhaku_lovers'},
            # {'mid': '2511', 'vote': 'up', 'slug': 'white_angel'},
            # {'mid': '4309', 'vote': 'up', 'slug': 'tomariba'},
            # {'mid': '2561', 'vote': 'up', 'slug': 'minna_no_oneesan'},
            # {'mid': '2830', 'vote': 'up', 'slug': 'maid_club'},
            # {'mid': '2177', 'vote': 'up', 'slug': 'harem_castle'},
            # {'mid': '5975', 'vote': 'up', 'slug': 'family_play_o_ri'},
            # {'mid': '45241', 'vote': 'up', 'slug': 'milk_hunters'},
            # {'mid': '18917', 'vote': 'up', 'slug': 'milk_angels'},
            # {'mid': '6169', 'vote': 'up', 'slug': 'leave_it_to_angel'},
            # {'mid': '2292', 'vote': 'up', 'slug': 'sweet_days_takasugi_kou'},
            # {'mid': '22580', 'vote': 'up', 'slug': 'mysthaven'},
            # {'mid': '5551', 'vote': 'up', 'slug': 'my_mother'},
            # {'mid': '16932', 'vote': 'up', 'slug': 'mumyou_no_uzu'},
            # {'mid': '12716', 'vote': 'up', 'slug': 'mama_to_sensei'},
            # {'mid': '9786', 'vote': 'up', 'slug': 'madam_palace'},
            # {'mid': '8679', 'vote': 'up', 'slug': 'ketsuen_jukujo'},
            # {'mid': '16600', 'vote': 'up', 'slug': 'insects_that_gathered_around_the_honey'},
            # {'mid': '13366', 'vote': 'up', 'slug': 'ingi_no_hate'},
            # {'mid': '3764', 'vote': 'up', 'slug': 'immorality_love_hole'},
            # {'mid': '12995', 'vote': 'up', 'slug': 'etsuraku_no_tobira'},
            # {'mid': '17616', 'vote': 'up', 'slug': 'estral_mature_woman'},
            # {'mid': '9893', 'vote': 'up', 'slug': 'dream_reality'},
            # {'mid': '2125', 'vote': 'up', 'slug': 'as_mama_likes_it'},
            {'mid': '4945', 'vote': 'up', 'slug': 'abno_madams'},
            # {'mid': '4682', 'vote': 'up', 'slug': 'the_pretty_peach_hip'},
            {'mid': '2239', 'vote': 'up', 'slug': 'mizugi_kanojo'},
            {'mid': '4061', 'vote': 'up', 'slug': 'chu_chu_cherry'},
            # {'mid': '21434', 'vote': 'up', 'slug': 'the_archangel_of_love_love_mary'},
            # {'mid': '31845', 'vote': 'up', 'slug': 'lust_kiss'},
            # {'mid': '28496', 'vote': 'up', 'slug': 'lovemare_ge'},
            # {'mid': '24005', 'vote': 'up', 'slug': 'lovemare_jou'},
            # {'mid': '40603', 'vote': 'up', 'slug': 'otherworld_harem_paradise'},
            # {'mid': '52251', 'vote': 'up', 'slug': 'hands_on_draining_with_three_succubus_sister'},
            # {'mid': '3261', 'vote': 'up', 'slug': 'dorei_usagi_to_anthony'},
            # {'mid': '4644', 'vote': 'up', 'slug': 'beautiful_girls_club'},
            # {'mid': '4822', 'vote': 'up', 'slug': 'shoujo_x_shoujo_x_shoujo'},
            # {'mid': '13736', 'vote': 'up', 'slug': 'lingua_franca'},
            # {'mid': '3252', 'vote': 'up', 'slug': 'pour_me_milk'},
            # {'mid': '61454', 'vote': 'up', 'slug': 'yuita_ma'},
            # {'mid': '17133', 'vote': 'up', 'slug': 'sister_breeder'},
            # {'mid': '50107', 'vote': 'up', 'slug': 'ima_real'},
            # {'mid': '60408', 'vote': 'up', 'slug': 'takane_tama'},
            # {'mid': '7321', 'vote': 'up', 'slug': 'sutotama'},
            # {'mid': '4491', 'vote': 'up', 'slug': 'sakitama'},
            # {'mid': '13974', 'vote': 'up', 'slug': 'reitama'},
            # {'mid': '60371', 'vote': 'up', 'slug': 'outama_king_of_soul'},
            # {'mid': '19913', 'vote': 'up', 'slug': 'maritama_renshuuchou'},
            # {'mid': '14978', 'vote': 'up', 'slug': 'mana_tama_plus'},
            # {'mid': '4483', 'vote': 'up', 'slug': 'mamotama'},
            # {'mid': '19072', 'vote': 'up', 'slug': 'maitama'},
            # {'mid': '9505', 'vote': 'up', 'slug': 'eritama_eri_love_middleage'},
            # {'mid': '4472', 'vote': 'up', 'slug': 'doritama'},
            {'mid': '11853', 'vote': 'up', 'slug': 'misgard_feoh'},
            
            # {'mid': '23377', 'vote': 'up', 'slug': 'c93_rakugakichou'},
            # {'mid': '25289', 'vote': 'up', 'slug': 'akanes_in_a_pinch'},
            # {'mid': '8751', 'vote': 'up', 'slug': 'yui_chan_to_issho'},
            # {'mid': '2507', 'vote': 'up', 'slug': 'toraburu_soushuuhen'},
            # {'mid': '3327', 'vote': 'up', 'slug': 'nakaba'},
            # {'mid': '6971', 'vote': 'up', 'slug': 'titikei'},
            # {'mid': '3811', 'vote': 'up', 'slug': 'insei_iroiro'},
            # {'mid': '3326', 'vote': 'up', 'slug': 'mikanal'},
            # {'mid': '4058', 'vote': 'up', 'slug': 'harimaro'},
            # {'mid': '3311', 'vote': 'up', 'slug': 'harima_x'},
            # {'mid': '3305', 'vote': 'up', 'slug': 'cambell_juice'},
            # {'mid': '34179', 'vote': 'up', 'slug': 'bujideta'},
            # {'mid': '50945', 'vote': 'up', 'slug': 'konoha_don_tokumori'},
            # {'mid': '16444', 'vote': 'up', 'slug': 'ble_nana'},
            # {'mid': '47688', 'vote': 'up', 'slug': 'kage_hinate_ni_sakura_saku'},
            # {'mid': '10605', 'vote': 'up', 'slug': 'toushatei_naruto'},
            # {'mid': '44687', 'vote': 'up', 'slug': 'pink_no_bakajikara'},
            # {'mid': '5533', 'vote': 'up', 'slug': 'saboten_nindou'},
            # {'mid': '14079', 'vote': 'up', 'slug': 'saboten_campus'},
            # {'mid': '48453', 'vote': 'up', 'slug': 'saboten'},
            # {'mid': '55886', 'vote': 'up', 'slug': 'narutophole'},
            # {'mid': '58418', 'vote': 'up', 'slug': 'narutop_pink'},
            # {'mid': '49259', 'vote': 'up', 'slug': 'konoha_don'},
            # {'mid': '45222', 'vote': 'up', 'slug': 'konoha_saboten'},
            # {'mid': '45488', 'vote': 'up', 'slug': 'inniku_koushin'},
            # {'mid': '31371', 'vote': 'up', 'slug': 'ikimono_gakari'},
            # {'mid': '48617', 'vote': 'up', 'slug': 'hyakugo_no_jutsu'},
            # {'mid': '32567', 'vote': 'up', 'slug': 'haouju_saboten'},
            # {'mid': '21123', 'vote': 'up', 'slug': 'botan_to_sakura'},
            # {'mid': '25373', 'vote': 'up', 'slug': 'arashi_no_bouken'},
            # {'mid': '56849', 'vote': 'up', 'slug': 'pink_yu_gi'},
            # {'mid': '56203', 'vote': 'up', 'slug': 'black_magician_girl_forced_orgasm_duel'},
            # {'mid': '25628', 'vote': 'up', 'slug': 'dark_ceremony_edition'},
            # {'mid': '32997', 'vote': 'up', 'slug': 'endless_my_turn'},
            # {'mid': '60792', 'vote': 'up', 'slug': 'iron_rose'},
            # {'mid': '20630', 'vote': 'up', 'slug': 'ishizus_secret_draw'},
            # {'mid': '44421', 'vote': 'up', 'slug': 'naughty_anime_r'},
            # {'mid': '26647', 'vote': 'up', 'slug': 'overlay_magic'},
            # {'mid': '28713', 'vote': 'up', 'slug': 'pleasure_game'},
            # {'mid': '36189', 'vote': 'up', 'slug': 'seinen_miracle_jump'},
            # {'mid': '35643', 'vote': 'up', 'slug': 'sex_life_with_servant_bmg'},
            # {'mid': '47561', 'vote': 'up', 'slug': 'together_with_dark_magician_girl'},
        
            # {'mid': '17035', 'vote': 'up', 'slug': 'kage_hinata_ni_saku'},
            # {'mid': '36608', 'vote': 'up', 'slug': 'karakishi_youhen_dan_compliation'},
            # {'mid': '18065', 'vote': 'up', 'slug': 'orange_pie'},
            # {'mid': '3464', 'vote': 'up', 'slug': 'ai_koukaishi'},
            # {'mid': '45392', 'vote': 'up', 'slug': 'a_big_breasted_oni_girls_first_time_having_sex'},
            # {'mid': '3190', 'vote': 'up', 'slug': 'bonneys_defeat'},
            # {'mid': '31692', 'vote': 'up', 'slug': 'chop_stick'},
            # {'mid': '9684', 'vote': 'up', 'slug': 'dorei_kentoushi_rebecca'},
            # {'mid': '5568', 'vote': 'up', 'slug': 'grandline_chronicle_colorful_sainyuu'},
            # {'mid': '8211', 'vote': 'up', 'slug': 'instinct_world'},
            # {'mid': '33114', 'vote': 'up', 'slug': 'kaizoku_jingi'},
            # {'mid': '11189', 'vote': 'up', 'slug': 'koukai_soushuuhen'},
            # {'mid': '15447', 'vote': 'up', 'slug': 'love_koukaishi'},
            # {'mid': '3201', 'vote': 'up', 'slug': 'love_love_hurricane'},
            # {'mid': '3781', 'vote': 'up', 'slug': 'love_2_hurricane'},
            # {'mid': '6012', 'vote': 'up', 'slug': 'mero_mero_girls_new_world'},
            # {'mid': '33046', 'vote': 'up', 'slug': 'oonami_ni_norou'},
            # {'mid': '33047', 'vote': 'up', 'slug': 'op_sex'},
            # {'mid': '3541', 'vote': 'up', 'slug': 'snake_princess'},
            # {'mid': '4167', 'vote': 'up', 'slug': 'through_the_wall'},
            # {'mid': '15703', 'vote': 'up', 'slug': 'two_piece_nami_vs_arlong'},
            # {'mid': '11117', 'vote': 'up', 'slug': 'weather_report_muten'},
            # {'mid': '62433', 'vote': 'up', 'slug': 'zoro_nami_sairoku'},
            # {'mid': '8743', 'vote': 'up', 'slug': 'anataga_nozomunara_watashi'},
            # {'mid': '19273', 'vote': 'up', 'slug': 'death_note_soushuuhen'},
            # {'mid': '24415', 'vote': 'up', 'slug': 'ff_fight'},
            # {'mid': '22615', 'vote': 'up', 'slug': 'tifa_sai'},
            # {'mid': '3548', 'vote': 'up', 'slug': 'tifa_hard'},
            # {'mid': '3547', 'vote': 'up', 'slug': 'tifa_climax'},
            # {'mid': '3546', 'vote': 'up', 'slug': 'tifa_before_climax'},
            # {'mid': '3549', 'vote': 'up', 'slug': 'uzumaki_hanataba'},
            # {'mid': '7726', 'vote': 'up', 'slug': 'virgin_idol'},
            # {'mid': '3518', 'vote': 'up', 'slug': 'hinata'},
            # {'mid': '19075', 'vote': 'up', 'slug': 'the_only_shame'},
            # {'mid': '38088', 'vote': 'up', 'slug': 'an_ancient_tradition_young_wife_is_harassed'},
            # {'mid': '6818', 'vote': 'up', 'slug': '18_gou_ga_saimin_ge_ntr_reru_hon'},
            # {'mid': '25894', 'vote': 'up', 'slug': '2_for_1_delicious_fun'},
            # {'mid': '67969', 'vote': 'up', 'slug': '2x1_lunch'},
            # {'mid': '38992', 'vote': 'up', 'slug': 'aim_at_planet_nameki'},
            # {'mid': '52330', 'vote': 'up', 'slug': 'android_eighteen_vs_master_roshi'},
            # {'mid': '25265', 'vote': 'up', 'slug': 'android_21s_remodeling_plan'},
            # {'mid': '16443', 'vote': 'up', 'slug': 'android_n18_and_mrsatan'},
            # {'mid': '53067', 'vote': 'up', 'slug': 'babys_revenge'},
            # {'mid': '66973', 'vote': 'up', 'slug': 'beerus_yamamoto'},
            # {'mid': '5898', 'vote': 'up', 'slug': 'between_the_lines'},
            # {'mid': '29014', 'vote': 'up', 'slug': 'bitch_girlfriend'},
            # {'mid': '32518', 'vote': 'up', 'slug': 'black_defeats_the_hero_of_the_future_the_sacrifice_of_the_faithful_bride'},
            # {'mid': '38101', 'vote': 'up', 'slug': 'bulma_and_friends'},
            # {'mid': '46102', 'vote': 'up', 'slug': 'bulma_meets_mr_popo_sex_inside_the_mysterious_spaceship'},
            # {'mid': '40083', 'vote': 'up', 'slug': 'bulma_no_saikyou_e_no_michi'},
            # {'mid': '68445', 'vote': 'up', 'slug': 'bulma_vs_general_blue'},
            # {'mid': '64873', 'vote': 'up', 'slug': 'bulma_x_oolong'},
            # {'mid': '44847', 'vote': 'up', 'slug': 'bunny_girl_transformation'},
            # {'mid': '57409', 'vote': 'up', 'slug': 'burning_road'},
            # {'mid': '24237', 'vote': 'up', 'slug': 'busty_android_wants_to_dominate_the_world'},
            # {'mid': '32850', 'vote': 'up', 'slug': 'cell_no_esa'},
            # {'mid': '66127', 'vote': 'up', 'slug': 'change_yamamoto'},
            # {'mid': '63417', 'vote': 'up', 'slug': 'chichi_chi_chichi'},
            # {'mid': '25103', 'vote': 'up', 'slug': 'dangan_ball'},
            # {'mid': '4473', 'vote': 'up', 'slug': 'dragon_award'},
            # {'mid': '11101', 'vote': 'up', 'slug': 'dragon_ball_eb'},
            # {'mid': '11786', 'vote': 'up', 'slug': 'dragon_ball_h'},
            # {'mid': '30215', 'vote': 'up', 'slug': 'dragon_ball_having_sex_with_your_lovers_mom'},
            # {'mid': '12957', 'vote': 'up', 'slug': 'dragon_road'},
            # {'mid': '51540', 'vote': 'up', 'slug': 'dragon_road_fivehundredfiftyfive'},
            # {'mid': '51505', 'vote': 'up', 'slug': 'dragonball_h_bessatsu_soushuuhen'},
            # {'mid': '20475', 'vote': 'up', 'slug': 'dragonball_h_extra_issue'},
            # {'mid': '53098', 'vote': 'up', 'slug': 'episode_of_bulma'},
            # {'mid': '14675', 'vote': 'up', 'slug': 'eromangirl'},
            # {'mid': '60073', 'vote': 'up', 'slug': 'fake_namekians'},
            # {'mid': '40131', 'vote': 'up', 'slug': 'fight_in_the_sixth_universe'},
            # {'mid': '44526', 'vote': 'up', 'slug': 'future_sex_gohan_bulma'},
            # {'mid': '47565', 'vote': 'up', 'slug': 'gohan_vs_erasa'},
            # {'mid': '31470', 'vote': 'up', 'slug': 'hoheto'},
            # {'mid': '22217', 'vote': 'up', 'slug': 'its_hard_work'},
            # {'mid': '14276', 'vote': 'up', 'slug': 'kame_sennin_no_bitch'},
            # {'mid': '63566', 'vote': 'up', 'slug': 'lots_of_sex_in_the_future'},
            # {'mid': '44958', 'vote': 'up', 'slug': 'lunch_black_love'},
            # {'mid': '49558', 'vote': 'up', 'slug': 'mister_satans_secret_training'},
            # {'mid': '44988', 'vote': 'up', 'slug': 'nam_vs_ranfan'},
            # {'mid': '67484', 'vote': 'up', 'slug': 'no_one_can_go_against_beerus'},
            # {'mid': '56434', 'vote': 'up', 'slug': 'no_one_disobeys_beerus'},
            # {'mid': '38926', 'vote': 'up', 'slug': 'oolong_cheats_on_bulma'},
            # {'mid': '58200', 'vote': 'up', 'slug': 'pafupafu_dragon_ball_z_versus'},
            # {'mid': '63881', 'vote': 'up', 'slug': 'paradise_or_hell_snake_princess_hospitality'},
            # {'mid': '34000', 'vote': 'up', 'slug': 'punishment_in_pilafs_castle'},
            # {'mid': '26827', 'vote': 'up', 'slug': 'rape_the_heroine'},
            # {'mid': '44818', 'vote': 'up', 'slug': 'ryona_budokai'},
            # {'mid': '48312', 'vote': 'up', 'slug': 'sex_in_the_bath'},
            # {'mid': '60110', 'vote': 'up', 'slug': 'sex_in_the_bathroom'},
            # {'mid': '16211', 'vote': 'up', 'slug': 'shinmai_dragon_night'},
            # {'mid': '41572', 'vote': 'up', 'slug': 'tanjou_aku_no_onna_senshi'},
            # {'mid': '45061', 'vote': 'up', 'slug': 'the_evil_brother'},
            # {'mid': '51992', 'vote': 'up', 'slug': 'the_strongest_mom_ever_wants_to_earn_some_money'},
            # {'mid': '22888', 'vote': 'up', 'slug': 'videl_vs_spopovich'},
            # {'mid': '62978', 'vote': 'up', 'slug': 'xx_dragon_ball'},
            # {'mid': '8274', 'vote': 'up', 'slug': 'fuck_muscleman'},
            # {'mid': '32251', 'vote': 'up', 'slug': 'edo_higan'},
            # {'mid': '19875', 'vote': 'up', 'slug': 'i_refuse_maybe'},
            # {'mid': '3524', 'vote': 'up', 'slug': 'kasshoku_no_koibito'},
            # {'mid': '3870', 'vote': 'up', 'slug': 'nel'},
            # {'mid': '5045', 'vote': 'up', 'slug': 'orihime_chan_de_go'},
            # {'mid': '3536', 'vote': 'up', 'slug': 'sariban_no_hasai_nichi'},
            # {'mid': '3553', 'vote': 'up', 'slug': 'watashi_wa_kyozetsu_suru_kamo'},
            # {'mid': '29386', 'vote': 'up', 'slug': 'yorunekosan_no_shukou_raijuu_ikaryaku'},
        ]
        
        
        # 3. Defina o ALVO único para todas as requisições
        # TARGET = {
        #     'mid': 8988,
        #     'vote': 'up',
        #     'slug': 'made_in_heaven' # Usado para o header 'referer'
        # }
        TARGET = ALVOS[0]
        # Para mudar o alvo, basta editar este dicionário. Exemplo:
        # TARGET = {'mid': 3032, 'vote': 'up', 'slug': 'pearl_jam'}
        
        
        # --- CONFIGURAÇÕES DA REQUISIÇÃO (definidas apenas uma vez) ---
        URL = 'https://hentai2read.com/api'
        
        # Cookies podem ser definidos aqui se necessário
        COOKIES = {}
        
        def make_request(worker_id, target_info):
            """
            Função executada por cada thread. Envia uma requisição POST para o alvo definido.
            """
            # Monta o corpo (payload) da requisição com base nas informações do alvo
        
            HEADERS = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'pt-BR,pt;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://hentai2read.com',
                'priority': 'u=1, i',
                'referer': f'https://hentai2read.com/{target_info["slug"]}/', # Referer dinâmico
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Chrome OS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
        
            data = {
                'controller': 'manga',
                'action': 'recommendation',
                'mid': str(target_info['mid']),
                'vote': target_info['vote'],
            }
        
            try:
                # tempo entre 15 e 15 segundos, 1 mais um random entre 0 e 5
                tempo = 0.1 + random.random()
                time.sleep(tempo)
                response = requests.post(URL, headers=HEADERS, cookies=COOKIES, data=data)
                response.raise_for_status()  # Levanta um erro para status HTTP 4xx ou 5xx
        
                # Tenta decodificar a resposta como JSON
                try:
                    response_data = response.json()
                    if worker_id %100 == 0:
                        pass
                        # print(f"[Thread {worker_id}] Sucesso! MID: {target_info['mid']}, Voto: {target_info['vote']}, Status: {response.status_code}, Resposta: {response_data}")
                        # print(f"[Thread {worker_id}] Sucesso! MID: {target_info['mid']}, Voto: {target_info['vote']}, Status: {response.status_code}, Resposta: {response_data}")
                except ValueError:
                    # print(f"[Thread {worker_id}] Sucesso, mas resposta não é JSON! MID: {target_info['mid']}, Status: {response.status_code}, Resposta: {response.text}")
                    pass
        
        
                return f"MID {target_info['mid']} - Sucesso"
        
            except requests.exceptions.HTTPError as e:
                pass
                # print(f"[Thread {worker_id}] Erro HTTP! MID: {target_info['mid']}, Status: {e.response.status_code}, Resposta: {e.response.text}")
            except requests.exceptions.RequestException as e:
                # print(f"[Thread {worker_id}] ERRO na requisição! MID: {target_info['mid']}, Erro: {e}")
                pass
            return f"MID {target_info['mid']} - Erro"
        
        # --- EXECUÇÃO PRINCIPAL ---
        # if __name__ == "__main__":
        global alvo_atual
        # while True:
        #     # repetir smpte e exeutr s 6 e s 18h e minuto for 10
        #     if hora_atual := __import__('datetime').datetime.now().hour in [6, 13, 19, 22]:
        #         if __import__('datetime').datetime.now().minute == 28:
        #             # pervrre todos os alvos
        for alvo_atual2 in ALVOS:
            alvo_atual = alvo_atual2
            print(f"Iniciando {TOTAL_REQUESTS} requisições para o MID {alvo_atual['mid']} usando {NUM_THREADS} threads simultâneas...")
            UPS_VARIAVEIS = int(random.random()*MULTIPLIER)
            if alvo_atual['mid'] in EXTRA_UP:
                UPS_VARIAVEIS += MULTIPLIER
                if UPS_VARIAVEIS < 60000:
                    UPS_VARIAVEIS += MULTIPLIER
            if alvo_atual['mid'] in EXTRA_UP2:
                UPS_VARIAVEIS += MULTIPLIER
                if UPS_VARIAVEIS < 65000:
                    UPS_VARIAVEIS += MULTIPLIER*4
            if alvo_atual['mid'] in EXTRA_UP3:
                UPS_VARIAVEIS += MULTIPLIER
                if UPS_VARIAVEIS < 80000:
                    UPS_VARIAVEIS += MULTIPLIER*1000
            if alvo_atual['mid'] in EXTRA_PLUS:
                UPS_VARIAVEIS += 30000
                if UPS_VARIAVEIS < 200000:
                    UPS_VARIAVEIS += MULTIPLIER*1000
            if alvo_atual['mid'] in EXTRA_ULTRA:
                UPS_VARIAVEIS += 30000
                if UPS_VARIAVEIS < 500000:
                    UPS_VARIAVEIS += MULTIPLIER*10000
            print(f"Likes variaveis para o alvo {alvo_atual["slug"]}: {UPS_VARIAVEIS}")
            # Usa ThreadPoolExecutor para gerenciar um pool de threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                # Agenda a execução da função 'make_request' por 'TOTAL_REQUESTS' vezes.
                # O executor gerencia a fila, garantindo que no máximo 'NUM_THREADS'
                # sejam executadas ao mesmo tempo.
                futures = [executor.submit(make_request, i + 1, alvo_atual) for i in range(TOTAL_REQUESTS + UPS_VARIAVEIS)]
    
                # O bloco 'with' garante que o programa só continuará após
                # todas as 'TOTAL_REQUESTS' tarefas agendadas terminarem.
                concurrent.futures.wait(futures)
    
            print(f"Processo finalizado. {TOTAL_REQUESTS + UPS_VARIAVEIS} requisições foram enviadas.")
            time.sleep(2)
    def execute4():
        import requests
        import concurrent.futures
        
        # --- CONFIGURAÇÕES DO SCRIPT ---
        # O número de vezes que o ciclo de 40 requisições será repetido
        NUM_CICLOS = 1
        
        # O número de threads simultâneas a cada ciclo
        NUM_THREADS = 30
        
        # --- CONFIGURAÇÕES DA REQUISIÇÃO ---
        URL = 'https://hentai2read.com/api'
        
        # Lista de alvos. Você pode adicionar mais dicionários aqui.
        # O script usará o primeiro item da lista (alvo_atual).
        # ALVOS = [
        #     # {'mid': '8988', 'slug': 'made_in_heaven_jupiter'},
        #     # {'mid': '3675', 'slug': 'tubala_bells'},
        #     # {'mid': '3498', 'slug': 'sex_pistols'},
        #     # {'mid': '3032', 'slug': 'pearl_jam'},
        #     # {'mid': '3649', 'slug': 'beach_boy'},
        #     # {'mid': '3596', 'slug': 'welkome_to_tokoharusou'},
        #     {'mid': '26602', 'slug': 'love_triangle_z'},
        # ]
        ALVOS = [
            # {'mid': '8988', 'vote': 'up', 'slug': 'made_in_heaven_jupiter'},
            # {'mid': '3675', 'vote': 'up', 'slug': 'tubala_bells'},
            # {'mid': '3498', 'vote': 'up', 'slug': 'sex_pistols'},
            {'mid': '3032', 'vote': 'up', 'slug': 'pearl_jam'},
            {'mid': '27016', 'vote': 'up', 'slug': 'tales_of_harem_in_another_world'},
            {'mid': '5736', 'vote': 'up', 'slug': 'nangoku_harem'},
            {'mid': '4099', 'vote': 'up', 'slug': 'doa_harem'},
            {'mid': '10769', 'vote': 'up', 'slug': 'harem_variety_pack'},
            {'mid': '18483', 'vote': 'up', 'slug': 'p5_harem'},
            {'mid': '18222', 'vote': 'up', 'slug': 'fudeoro_sisters'},
            {'mid': '11611', 'vote': 'up', 'slug': 'i_am_everyones_landlord'},
            {'mid': '68870', 'vote': 'up', 'slug': 'i_cant_get_it_up_without_two_pairs_of_big_breasts'},
            {'mid': '6777', 'vote': 'up', 'slug': 'regrettable_heroines'},
            {'mid': '50438', 'vote': 'up', 'slug': 'sudden_harem_life_after'},
            {'mid': '21974', 'vote': 'up', 'slug': 'yukemuri_harem_monogatari'},
            {'mid': '44329', 'vote': 'up', 'slug': 'nanakas_paradise'},
            
            {'mid': '45432', 'vote': 'up', 'slug': 'elf_ni_inmon_o_tsukeru_hon'},
            {'mid': '21154', 'vote': 'up', 'slug': 'makipet'},
            {'mid': '22575', 'vote': 'up', 'slug': 'dangan_archive'},
            {'mid': '20203', 'vote': 'up', 'slug': 'shoujo_kaishun'},
            {'mid': '26338', 'vote': 'up', 'slug': 'bibi_collection'},
            
            # {'mid': '53149', 'vote': 'up', 'slug': 'hahaue_mo_mesu_orc'},
            # {'mid': '2004', 'vote': 'up', 'slug': 'blue_eyes'},
            {'mid': '14548', 'vote': 'up', 'slug': 'an_elder_sister'},
            {'mid': '21432', 'vote': 'up', 'slug': 'ane_naru_mono'},
            # kimi_wa_akogare_no_tawawa
            {'mid': '45050', 'vote': 'up', 'slug': 'sono_bisque_doll_wa_h_o_suru'},
            {'mid': '34594', 'vote': 'up', 'slug': 'rental_kanojo_osawari_shimasu'},
            {'mid': '3883', 'vote': 'up', 'slug': 'lovematio'},
            {'mid': '18482', 'vote': 'up', 'slug': 'sleeping_sister'},
            {'mid': '58872', 'vote': 'up', 'slug': 'kimi_wa_akogare_no_tawawa'},
            
            {'mid': '21990', 'vote': 'up', 'slug': 'bullied_revenge_hypnosis'},
            {'mid': '38779', 'vote': 'up', 'slug': 'family_control'},
            {'mid': '17542', 'vote': 'up', 'slug': 'hypnosis_sex_guidance'},
            {'mid': '31449', 'vote': 'up', 'slug': 'dakuon'},
            
            {'mid': '2572', 'vote': 'up', 'slug': 'pink_cherry_pie'},
            {'mid': '6731', 'vote': 'up', 'slug': 'mon_mon_animal_girl'},
            {'mid': '2431', 'vote': 'up', 'slug': 'momozono_gakuen'},
            {'mid': '4422', 'vote': 'up', 'slug': 'purupuru_milk_feeling'},
            {'mid': '31449', 'vote': 'up', 'slug': 'rental_kanojo_osawari_shimasu'},
            
        ]
        
        
        # Selecione o alvo para esta execução
        # alvo_atual = ALVOS[5] # Usando 'made_in_heaven'
        
        # Headers e Data são montados dinamicamente com base no alvo_atual
        # HEADERS = {
        #     'accept': 'application/json, text/javascript, */*; q=0.01',
        #     'accept-language': 'pt-BR,pt;q=0.9',
        #     'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        #     'origin': 'https://hentai2read.com',
        #     'priority': 'u=1, i',
        #     'referer': f'https://hentai2read.com/{alvo_atual["slug"]}/',
        #     'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        #     'sec-ch-ua-mobile': '?0',
        #     'sec-ch-ua-platform': '"Chrome OS"',
        #     'sec-fetch-dest': 'empty',
        #     'sec-fetch-mode': 'cors',
        #     'sec-fetch-site': 'same-origin',
        #     'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        #     'x-requested-with': 'XMLHttpRequest',
        # }
        
        # COOKIES = {
        #     'pfs': '11101100100',
        #     'zone-closed-5160176': 'true',
        #     'zone-cap-5181220': '1;1761245087',
        # }
        
        # DATA = {
        #     'controller': 'manga',
        #     # 'action': 'views',
        #     'action': 'rating',
        #     'mid': alvo_atual['mid'],
        #     'score': '5000',
        # }
        
        
        def enviar_requisicao(worker_id, ciclo_atual):
            """
            Função que será executada por cada thread.
            Envia uma única requisição POST e trata a resposta.
            """
            try:
                response = requests.post(URL, headers=HEADERS, cookies=COOKIES, data=DATA)
                response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx ou 5xx
                if worker_id %1000 == 0:
                    print(f"[Ciclo {ciclo_atual} | Thread {worker_id}] Sucesso! Status: {response.status_code}, Resposta: {response.json()}")
                return response.status_code
        
            except requests.exceptions.HTTPError as e:
                print(f"[Ciclo {ciclo_atual} | Thread {worker_id}] Erro HTTP! Status: {e.response.status_code}, Resposta: {e.response.text}")
            except requests.exceptions.RequestException as e:
                print(f"[Ciclo {ciclo_atual} | Thread {worker_id}] ERRO na requisição: {e}")
            except ValueError: # Ocorre se response.json() falhar
                print(f"[Ciclo {ciclo_atual} | Thread {worker_id}] Resposta não é um JSON válido: {response.text}")
        
            return None
        
        # --- EXECUÇÃO DO SCRIPT ---
        # if __name__ == "__main__":
        for alvo_atual2 in ALVOS:
            print(f"Iniciando disparos para o alvo: {alvo_atual2['slug']} (mid: {alvo_atual2['mid']})")
            HEADERS = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'pt-BR,pt;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://hentai2read.com',
                'priority': 'u=1, i',
                'referer': f'https://hentai2read.com/{alvo_atual2["slug"]}/',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Chrome OS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
    
            COOKIES = {
                'pfs': '11101100100',
                'zone-closed-5160176': 'true',
                'zone-cap-5181220': '1;1761245087',
            }
            DATA = {
                'controller': 'manga',
                # 'action': 'views',
                'action': 'rating',
                'mid': alvo_atual2['mid'],
                'score': '999999999',
                # 'score': '50000',
            }
            for i in range(NUM_CICLOS):
                ciclo_num = i + 1
                print(f"--- INICIANDO CICLO {ciclo_num}/{NUM_CICLOS} ---")
    
                # Cria um pool de threads que executará as 40 tarefas
                with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                    # Submete a função 'enviar_requisicao' para ser executada 40 vezes em paralelo
                    futures = [executor.submit(enviar_requisicao, worker_id, ciclo_num) for worker_id in range(1, NUM_THREADS + 1)]
    
                    # O bloco 'with' aguarda a conclusão de todas as 40 threads
                    # antes de continuar para o próximo ciclo do loop 'for'
                    concurrent.futures.wait(futures)
    
                print(f"--- CICLO {ciclo_num}/{NUM_CICLOS} FINALIZADO ---\n")

    def execute3():    
        import requests
        import concurrent.futures
        import time
        import random
        import json
        
        # --- CONFIGURAÇÕES DO SCRIPT ---
        # 1. Defina o número TOTAL de requisições que você quer enviar
        TOTAL_REQUESTS = 200 #entre 1000 e 7000
        MULTIPLIER = 100
        EXTRA_UP = ['3041','45050','14548','21990','38779','5589','14126','2169','2184','2815','4195','10507','2630','2058','3252','4061','4757','3799','49826','41278','45432','53149','2004']
        EXTRA_UP2 = ['3041','5589','2169','2815','3799','4195','3252','49826','41278','45432','53149','2004','45050','14548','21990','38779']
        EXTRA_PLUS = ['14548','5589','3032','3649','3662','3648','8988','3041','14548',]
        # 2. Defina quantas requisições devem ser executadas SIMULTANEAMENTE (threads)
        NUM_THREADS = 200
        # 3041tower_of_gray
        # 2905yellow_temperance
        # 3662scary_monsters
        # 10614 shidare_zakura
        # 48973 hypnotism_is_just_make_believe
        # 3648 aqua_necklace
        # 3685 burning_down_the_house
        # 3654 in_a_silent_way
        ALVOS = [
            # {'mid': '49826', 'vote': 'up', 'slug': 'my_little_sisters_are_slutty_orcs'},
            # {'mid': '41278', 'vote': 'up', 'slug': 'horny_isekai_elfs_evil_eye'},
# tales_of_harem_in_another_world
            {'mid': '27016', 'vote': 'up', 'slug': 'tales_of_harem_in_another_world'},
            {'mid': '5736', 'vote': 'up', 'slug': 'nangoku_harem'},
            {'mid': '4099', 'vote': 'up', 'slug': 'doa_harem'},
            {'mid': '10769', 'vote': 'up', 'slug': 'harem_variety_pack'},
            {'mid': '18483', 'vote': 'up', 'slug': 'p5_harem'},
            {'mid': '18222', 'vote': 'up', 'slug': 'fudeoro_sisters'},
            {'mid': '11611', 'vote': 'up', 'slug': 'i_am_everyones_landlord'},
            {'mid': '68870', 'vote': 'up', 'slug': 'i_cant_get_it_up_without_two_pairs_of_big_breasts'},
            {'mid': '6777', 'vote': 'up', 'slug': 'regrettable_heroines'},
            {'mid': '50438', 'vote': 'up', 'slug': 'sudden_harem_life_after'},
            {'mid': '21974', 'vote': 'up', 'slug': 'yukemuri_harem_monogatari'},
            {'mid': '44329', 'vote': 'up', 'slug': 'nanakas_paradise'},
            
            {'mid': '45432', 'vote': 'up', 'slug': 'elf_ni_inmon_o_tsukeru_hon'},
            {'mid': '21154', 'vote': 'up', 'slug': 'makipet'},
            {'mid': '22575', 'vote': 'up', 'slug': 'dangan_archive'},
            {'mid': '20203', 'vote': 'up', 'slug': 'shoujo_kaishun'},
            {'mid': '26338', 'vote': 'up', 'slug': 'bibi_collection'},
            
            # {'mid': '53149', 'vote': 'up', 'slug': 'hahaue_mo_mesu_orc'},
            # {'mid': '2004', 'vote': 'up', 'slug': 'blue_eyes'},
            {'mid': '14548', 'vote': 'up', 'slug': 'an_elder_sister'},
            {'mid': '21432', 'vote': 'up', 'slug': 'ane_naru_mono'},
            # kimi_wa_akogare_no_tawawa
            {'mid': '45050', 'vote': 'up', 'slug': 'sono_bisque_doll_wa_h_o_suru'},
            {'mid': '34594', 'vote': 'up', 'slug': 'rental_kanojo_osawari_shimasu'},
            {'mid': '3883', 'vote': 'up', 'slug': 'lovematio'},
            {'mid': '18482', 'vote': 'up', 'slug': 'sleeping_sister'},
            {'mid': '58872', 'vote': 'up', 'slug': 'kimi_wa_akogare_no_tawawa'},
            
            {'mid': '21990', 'vote': 'up', 'slug': 'bullied_revenge_hypnosis'},
            {'mid': '38779', 'vote': 'up', 'slug': 'family_control'},
            {'mid': '17542', 'vote': 'up', 'slug': 'hypnosis_sex_guidance'},
            {'mid': '31449', 'vote': 'up', 'slug': 'dakuon'},
            
            {'mid': '2572', 'vote': 'up', 'slug': 'pink_cherry_pie'},
            {'mid': '6731', 'vote': 'up', 'slug': 'mon_mon_animal_girl'},
            {'mid': '2431', 'vote': 'up', 'slug': 'momozono_gakuen'},
            {'mid': '4422', 'vote': 'up', 'slug': 'purupuru_milk_feeling'},
            {'mid': '31449', 'vote': 'up', 'slug': 'rental_kanojo_osawari_shimasu'},
            
            
            {'mid': '8988', 'vote': 'up', 'slug': 'made_in_heaven_jupiter'},#an_elder_sister
            {'mid': '3675', 'vote': 'up', 'slug': 'tubala_bells'},
            {'mid': '3498', 'vote': 'up', 'slug': 'sex_pistols'},
            {'mid': '3032', 'vote': 'up', 'slug': 'pearl_jam'},
            {'mid': '3649', 'vote': 'up', 'slug': 'beach_boy'},
            {'mid': '3596', 'vote': 'up', 'slug': 'welcome_to_tokoharusou'},
            {'mid': '3662', 'vote': 'up', 'slug': 'scary_monsters'},
            # {'mid': '2905', 'vote': 'up', 'slug': 'yellow_temperance'},
            {'mid': '3041', 'vote': 'up', 'slug': 'tower_of_gray'},
            {'mid': '10614', 'vote': 'up', 'slug': 'shidare_zakura'},
            # {'mid': '48973', 'vote': 'up', 'slug': 'hypnotism_is_just_make_believe'},
            # {'mid': '3648', 'vote': 'up', 'slug': 'aqua_necklace'},
            # {'mid': '3685', 'vote': 'up', 'slug': 'burning_down_the_house'},
            # {'mid': '3654', 'vote': 'up', 'slug': 'in_a_silent_way'},
            # {'mid': '26602', 'vote': 'up', 'slug': 'love_triangle_z'},#ano_hi_no_tegomesan
            # {'mid': '13486', 'vote': 'up', 'slug': 'ano_hi_no_tegomesan'},
            # {'mid': '7639', 'vote': 'up', 'slug': 'another_one_bite_the_dust'},
            # {'mid': '3650', 'vote': 'up', 'slug': 'cream_starter'},
            # {'mid': '33288', 'vote': 'up', 'slug': 'flirtation_sped_forward'},
            # {'mid': '13234', 'vote': 'up', 'slug': 'game_of_lust'},
            # {'mid': '2718', 'vote': 'up', 'slug': 'sailor_moon_gold_experience'},
            # {'mid': '3486', 'vote': 'up', 'slug': 'hierophant_green'},
            # {'mid': '63520', 'vote': 'up', 'slug': 'just_for_tonight_ill_be_your_bitch'},
            # {'mid': '19443', 'vote': 'up', 'slug': 'kayoubi_no_yurameki'},
            # {'mid': '14074', 'vote': 'up', 'slug': 'magicians_red'},
            # {'mid': '3655', 'vote': 'up', 'slug': 'killer_queen'},
            # {'mid': '3017', 'vote': 'up', 'slug': 'diver_down'},
            # {'mid': '40339', 'vote': 'up', 'slug': 'oasis_kuroinu_juu'},
            # {'mid': '22442', 'vote': 'up', 'slug': 'ojisan_to_futarikiri'},
            # {'mid': '3722', 'vote': 'up', 'slug': 'red_hot_chili_peppers'},
            # {'mid': '3036', 'vote': 'up', 'slug': 'sheer_heart_attack'},
            # {'mid': '3665', 'vote': 'up', 'slug': 'sky_high'},
            {'mid': '5589', 'vote': 'up', 'slug': 'soft_and_wet'},
            # {'mid': '8040', 'vote': 'up', 'slug': 'submission_super_moon'},
            # {'mid': '3671', 'vote': 'up', 'slug': 'superfly'},
            # {'mid': '33063', 'vote': 'up', 'slug': 'tohth'},
        
            # {'mid': '2980', 'vote': 'up', 'slug': 'atum'},
            # {'mid': '16189', 'vote': 'up', 'slug': 'chocolate_disco'},
            # {'mid': '31185', 'vote': 'up', 'slug': 'queen_of_spades'},
            {'mid': '24414', 'vote': 'up', 'slug': 'saturday_girls_cant_hold_it_in'},
            {'mid': '46948', 'vote': 'up', 'slug': 'sweet_hearts_lesson'},
            {'mid': '2668', 'vote': 'up', 'slug': 'sweet_hearts_kisaragi_gunma'},
            {'mid': '2815', 'vote': 'up', 'slug': 'mai_favorite'},
            {'mid': '2220', 'vote': 'up', 'slug': 'love_selection'},
            # {'mid': '14126', 'vote': 'up', 'slug': 'hina_project'},#
            {'mid': '2169', 'vote': 'up', 'slug': 'giri_giri_sisters'},
            # {'mid': '3753', 'vote': 'up', 'slug': 'strawberry_panic'},
            # {'mid': '3770', 'vote': 'up', 'slug': 'kozue_panic'},
        
            # {'mid': '19129', 'vote': 'up', 'slug': 'milf_of_steel'},
            # {'mid': '17689', 'vote': 'up', 'slug': 'amazing_eighth_wonder'},
            {'mid': '20876', 'vote': 'up', 'slug': 'dont_meddle_in_my_daughter'},
            # {'mid': '32975', 'vote': 'up', 'slug': 'uncanny_eighthwonder'},
            {'mid': '17279', 'vote': 'up', 'slug': 'oyako_heroine_funtousu'},
            {'mid': '10507', 'vote': 'up', 'slug': 'one_hurricane'},
            {'mid': '62736', 'vote': 'up', 'slug': 'daughter_falling_into_stepfather'},
            # {'mid': '9272', 'vote': 'up', 'slug': 'the_working_goddess'},
            {'mid': '34689', 'vote': 'up', 'slug': 'icha_icha_unbalance'},
            {'mid': '4029', 'vote': 'up', 'slug': 'kan_ni_sakura'},
            # {'mid': '4191', 'vote': 'up', 'slug': 'yuri_and_friends_full_color'},
            # {'mid': '39860', 'vote': 'up', 'slug': 'the_athena_and_friends_ninetynine'},
            # {'mid': '44020', 'vote': 'up', 'slug': 'the_yuri_and_friends_ninetysix'},
            # {'mid': '4176', 'vote': 'up', 'slug': 'hinako_max'},
            # {'mid': '4194', 'vote': 'up', 'slug': 'yuri_and_friends_mai_special'},
            # {'mid': '4195', 'vote': 'up', 'slug': 'mary_special'},
            # {'mid': '4190', 'vote': 'up', 'slug': 'yuri_and_friends'},
            {'mid': '3560', 'vote': 'up', 'slug': 'rei_slave_to_the_grind'},
            # {'mid': '2967', 'vote': 'up', 'slug': 'a_housewifes_temptation'},
            {'mid': '2630', 'vote': 'up', 'slug': 'cheerism'},
            {'mid': '2058', 'vote': 'up', 'slug': 'milk_mama'},
            {'mid': '2239', 'vote': 'up', 'slug': 'mizugi_kanojo'},
            {'mid': '4061', 'vote': 'up', 'slug': 'chu_chu_cherry'},
            # {'mid': '21434', 'vote': 'up', 'slug': 'the_archangel_of_love_love_mary'},
            {'mid': '31845', 'vote': 'up', 'slug': 'lust_kiss'},
            {'mid': '28496', 'vote': 'up', 'slug': 'lovemare_ge'},
            {'mid': '24005', 'vote': 'up', 'slug': 'lovemare_jou'},
            # {'mid': '40603', 'vote': 'up', 'slug': 'otherworld_harem_paradise'},
            # {'mid': '3419', 'vote': 'up', 'slug': 'impossible'},
            {'mid': '4658', 'vote': 'up', 'slug': 'momoiro_passion'},
            {'mid': '2245', 'vote': 'up', 'slug': 'oh_miss_nanase'},
            # {'mid': '6483', 'vote': 'up', 'slug': 'my_neighbors_are_aliens'},
            # {'mid': '2055', 'vote': 'up', 'slug': 'maid_in_teacher'},
        
            {'mid': '19129', 'vote': 'up', 'slug': 'milf_of_steel'},
            {'mid': '17689', 'vote': 'up', 'slug': 'amazing_eighth_wonder'},
            {'mid': '20876', 'vote': 'up', 'slug': 'dont_meddle_in_my_daughter'},
            {'mid': '32975', 'vote': 'up', 'slug': 'uncanny_eighthwonder'},
            {'mid': '17279', 'vote': 'up', 'slug': 'oyako_heroine_funtousu'},
            {'mid': '3560', 'vote': 'up', 'slug': 'rei_slave_to_the_grind'},
            {'mid': '8039', 'vote': 'up', 'slug': 'st_dead_or_alive_highschool'},
            # {'mid': '5367', 'vote': 'up', 'slug': 'h.sas4'},
            # {'mid': '2630', 'vote': 'up', 'slug': 'cheerism'},
            {'mid': '2058', 'vote': 'up', 'slug': 'milk_mama'},
            {'mid': '2239', 'vote': 'up', 'slug': 'mizugi_kanojo'},
            {'mid': '4061', 'vote': 'up', 'slug': 'chu_chu_cherry'},
            # {'mid': '21434', 'vote': 'up', 'slug': 'the_archangel_of_love_love_mary'},
            # {'mid': '31845', 'vote': 'up', 'slug': 'lust_kiss'},
            # {'mid': '28496', 'vote': 'up', 'slug': 'lovemare_ge'},
            # {'mid': '24005', 'vote': 'up', 'slug': 'lovemare_jou'},
            # {'mid': '40603', 'vote': 'up', 'slug': 'otherworld_harem_paradise'},
            # {'mid': '52251', 'vote': 'up', 'slug': 'hands_on_draining_with_three_succubus_sister'},
            # {'mid': '3261', 'vote': 'up', 'slug': 'dorei_usagi_to_anthony'},
            # {'mid': '4644', 'vote': 'up', 'slug': 'beautiful_girls_club'},
            # {'mid': '4822', 'vote': 'up', 'slug': 'shoujo_x_shoujo_x_shoujo'},
            # {'mid': '13736', 'vote': 'up', 'slug': 'lingua_franca'},
            {'mid': '3252', 'vote': 'up', 'slug': 'pour_me_milk'},
            # {'mid': '61454', 'vote': 'up', 'slug': 'yuita_ma'},
            {'mid': '17133', 'vote': 'up', 'slug': 'sister_breeder'},
            {'mid': '50107', 'vote': 'up', 'slug': 'ima_real'},
            {'mid': '60408', 'vote': 'up', 'slug': 'takane_tama'},
            {'mid': '7321', 'vote': 'up', 'slug': 'sutotama'},
            {'mid': '4491', 'vote': 'up', 'slug': 'sakitama'},
            {'mid': '13974', 'vote': 'up', 'slug': 'reitama'},
            # {'mid': '60371', 'vote': 'up', 'slug': 'outama_king_of_soul'},
            # {'mid': '19913', 'vote': 'up', 'slug': 'maritama_renshuuchou'},
            {'mid': '14978', 'vote': 'up', 'slug': 'mana_tama_plus'},
            # {'mid': '4483', 'vote': 'up', 'slug': 'mamotama'},
            # {'mid': '19072', 'vote': 'up', 'slug': 'maitama'},
            # {'mid': '9505', 'vote': 'up', 'slug': 'eritama_eri_love_middleage'},
            {'mid': '4472', 'vote': 'up', 'slug': 'doritama'},
            {'mid': '11853', 'vote': 'up', 'slug': 'misgard_feoh'},
            
            # {'mid': '23377', 'vote': 'up', 'slug': 'c93_rakugakichou'},
            # {'mid': '25289', 'vote': 'up', 'slug': 'akanes_in_a_pinch'},
            # {'mid': '8751', 'vote': 'up', 'slug': 'yui_chan_to_issho'},
            # {'mid': '2507', 'vote': 'up', 'slug': 'toraburu_soushuuhen'},
            # {'mid': '3327', 'vote': 'up', 'slug': 'nakaba'},
            # {'mid': '6971', 'vote': 'up', 'slug': 'titikei'},
            # {'mid': '3811', 'vote': 'up', 'slug': 'insei_iroiro'},
            # {'mid': '3326', 'vote': 'up', 'slug': 'mikanal'},
            # {'mid': '4058', 'vote': 'up', 'slug': 'harimaro'},
            # {'mid': '3311', 'vote': 'up', 'slug': 'harima_x'},
            # {'mid': '3305', 'vote': 'up', 'slug': 'cambell_juice'},
            # {'mid': '34179', 'vote': 'up', 'slug': 'bujideta'},
            # {'mid': '50945', 'vote': 'up', 'slug': 'konoha_don_tokumori'},
            # {'mid': '16444', 'vote': 'up', 'slug': 'ble_nana'},
            # {'mid': '47688', 'vote': 'up', 'slug': 'kage_hinate_ni_sakura_saku'},
            # {'mid': '10605', 'vote': 'up', 'slug': 'toushatei_naruto'},
            # {'mid': '44687', 'vote': 'up', 'slug': 'pink_no_bakajikara'},
            # {'mid': '5533', 'vote': 'up', 'slug': 'saboten_nindou'},
            # {'mid': '14079', 'vote': 'up', 'slug': 'saboten_campus'},
            # {'mid': '48453', 'vote': 'up', 'slug': 'saboten'},
            # {'mid': '55886', 'vote': 'up', 'slug': 'narutophole'},
            # {'mid': '58418', 'vote': 'up', 'slug': 'narutop_pink'},
            # {'mid': '49259', 'vote': 'up', 'slug': 'konoha_don'},
            # {'mid': '45222', 'vote': 'up', 'slug': 'konoha_saboten'},
            # {'mid': '45488', 'vote': 'up', 'slug': 'inniku_koushin'},
            # {'mid': '31371', 'vote': 'up', 'slug': 'ikimono_gakari'},
            # {'mid': '48617', 'vote': 'up', 'slug': 'hyakugo_no_jutsu'},
            # {'mid': '32567', 'vote': 'up', 'slug': 'haouju_saboten'},
            # {'mid': '21123', 'vote': 'up', 'slug': 'botan_to_sakura'},
            # {'mid': '25373', 'vote': 'up', 'slug': 'arashi_no_bouken'},
            # {'mid': '56849', 'vote': 'up', 'slug': 'pink_yu_gi'},
            # {'mid': '56203', 'vote': 'up', 'slug': 'black_magician_girl_forced_orgasm_duel'},
            # {'mid': '25628', 'vote': 'up', 'slug': 'dark_ceremony_edition'},
            # {'mid': '32997', 'vote': 'up', 'slug': 'endless_my_turn'},
            # {'mid': '60792', 'vote': 'up', 'slug': 'iron_rose'},
            # {'mid': '20630', 'vote': 'up', 'slug': 'ishizus_secret_draw'},
            # {'mid': '44421', 'vote': 'up', 'slug': 'naughty_anime_r'},
            # {'mid': '26647', 'vote': 'up', 'slug': 'overlay_magic'},
            # {'mid': '28713', 'vote': 'up', 'slug': 'pleasure_game'},
            # {'mid': '36189', 'vote': 'up', 'slug': 'seinen_miracle_jump'},
            # {'mid': '35643', 'vote': 'up', 'slug': 'sex_life_with_servant_bmg'},
            # {'mid': '47561', 'vote': 'up', 'slug': 'together_with_dark_magician_girl'},
        
            # {'mid': '17035', 'vote': 'up', 'slug': 'kage_hinata_ni_saku'},
            {'mid': '36608', 'vote': 'up', 'slug': 'karakishi_youhen_dan_compliation'},
            {'mid': '18065', 'vote': 'up', 'slug': 'orange_pie'},
            {'mid': '3190', 'vote': 'up', 'slug': 'bonneys_defeat'},
            # {'mid': '31692', 'vote': 'up', 'slug': 'chop_stick'},
            # {'mid': '9684', 'vote': 'up', 'slug': 'dorei_kentoushi_rebecca'},
            # {'mid': '5568', 'vote': 'up', 'slug': 'grandline_chronicle_colorful_sainyuu'},
            {'mid': '8211', 'vote': 'up', 'slug': 'instinct_world'},
            # {'mid': '33114', 'vote': 'up', 'slug': 'kaizoku_jingi'},
            {'mid': '11189', 'vote': 'up', 'slug': 'koukai_soushuuhen'},
            {'mid': '3201', 'vote': 'up', 'slug': 'love_love_hurricane'},
            {'mid': '3781', 'vote': 'up', 'slug': 'love_2_hurricane'},
            {'mid': '6012', 'vote': 'up', 'slug': 'mero_mero_girls_new_world'},
            {'mid': '3541', 'vote': 'up', 'slug': 'snake_princess'},
            {'mid': '22615', 'vote': 'up', 'slug': 'tifa_sai'},
            {'mid': '3548', 'vote': 'up', 'slug': 'tifa_hard'},
            {'mid': '3547', 'vote': 'up', 'slug': 'tifa_climax'},
            {'mid': '3546', 'vote': 'up', 'slug': 'tifa_before_climax'},
            # {'mid': '3549', 'vote': 'up', 'slug': 'uzumaki_hanataba'},
            {'mid': '7726', 'vote': 'up', 'slug': 'virgin_idol'},
            # {'mid': '3518', 'vote': 'up', 'slug': 'hinata'},
            {'mid': '19075', 'vote': 'up', 'slug': 'the_only_shame'},
            # {'mid': '38088', 'vote': 'up', 'slug': 'an_ancient_tradition_young_wife_is_harassed'},
            # {'mid': '6818', 'vote': 'up', 'slug': '18_gou_ga_saimin_ge_ntr_reru_hon'},
            # {'mid': '25894', 'vote': 'up', 'slug': '2_for_1_delicious_fun'},
            {'mid': '67969', 'vote': 'up', 'slug': '2x1_lunch'},
            # {'mid': '38992', 'vote': 'up', 'slug': 'aim_at_planet_nameki'},
            {'mid': '52330', 'vote': 'up', 'slug': 'android_eighteen_vs_master_roshi'},
            # {'mid': '25265', 'vote': 'up', 'slug': 'android_21s_remodeling_plan'},
            # {'mid': '16443', 'vote': 'up', 'slug': 'android_n18_and_mrsatan'},
            {'mid': '53067', 'vote': 'up', 'slug': 'babys_revenge'},
            # {'mid': '66973', 'vote': 'up', 'slug': 'beerus_yamamoto'},
            # {'mid': '5898', 'vote': 'up', 'slug': 'between_the_lines'},
            # {'mid': '29014', 'vote': 'up', 'slug': 'bitch_girlfriend'},
            # {'mid': '32518', 'vote': 'up', 'slug': 'black_defeats_the_hero_of_the_future_the_sacrifice_of_the_faithful_bride'},
            # {'mid': '38101', 'vote': 'up', 'slug': 'bulma_and_friends'},
            # {'mid': '46102', 'vote': 'up', 'slug': 'bulma_meets_mr_popo_sex_inside_the_mysterious_spaceship'},
            # {'mid': '40083', 'vote': 'up', 'slug': 'bulma_no_saikyou_e_no_michi'},
            # {'mid': '68445', 'vote': 'up', 'slug': 'bulma_vs_general_blue'},
            # {'mid': '64873', 'vote': 'up', 'slug': 'bulma_x_oolong'},
            {'mid': '44847', 'vote': 'up', 'slug': 'bunny_girl_transformation'},
            # {'mid': '57409', 'vote': 'up', 'slug': 'burning_road'},
            # {'mid': '24237', 'vote': 'up', 'slug': 'busty_android_wants_to_dominate_the_world'},
            # {'mid': '32850', 'vote': 'up', 'slug': 'cell_no_esa'},
            # {'mid': '66127', 'vote': 'up', 'slug': 'change_yamamoto'},
            # {'mid': '63417', 'vote': 'up', 'slug': 'chichi_chi_chichi'},
            {'mid': '25103', 'vote': 'up', 'slug': 'dangan_ball'},
            # {'mid': '4473', 'vote': 'up', 'slug': 'dragon_award'},
            # {'mid': '11101', 'vote': 'up', 'slug': 'dragon_ball_eb'},
            # {'mid': '11786', 'vote': 'up', 'slug': 'dragon_ball_h'},
            # {'mid': '30215', 'vote': 'up', 'slug': 'dragon_ball_having_sex_with_your_lovers_mom'},
            {'mid': '12957', 'vote': 'up', 'slug': 'dragon_road'},
            {'mid': '51540', 'vote': 'up', 'slug': 'dragon_road_fivehundredfiftyfive'},
            # {'mid': '60073', 'vote': 'up', 'slug': 'fake_namekians'},
            {'mid': '44526', 'vote': 'up', 'slug': 'future_sex_gohan_bulma'},
            # {'mid': '47565', 'vote': 'up', 'slug': 'gohan_vs_erasa'},
            # {'mid': '31470', 'vote': 'up', 'slug': 'hoheto'},
            {'mid': '22217', 'vote': 'up', 'slug': 'its_hard_work'},
            {'mid': '67484', 'vote': 'up', 'slug': 'no_one_can_go_against_beerus'},
            {'mid': '56434', 'vote': 'up', 'slug': 'no_one_disobeys_beerus'},
            # {'mid': '38926', 'vote': 'up', 'slug': 'oolong_cheats_on_bulma'},
            {'mid': '58200', 'vote': 'up', 'slug': 'pafupafu_dragon_ball_z_versus'},
            {'mid': '63881', 'vote': 'up', 'slug': 'paradise_or_hell_snake_princess_hospitality'},
            {'mid': '34000', 'vote': 'up', 'slug': 'punishment_in_pilafs_castle'},
        ]
        
        
        # 3. Defina o ALVO único para todas as requisições
        # TARGET = {
        #     'mid': 8988,
        #     'vote': 'up',
        #     'slug': 'made_in_heaven' # Usado para o header 'referer'
        # }
        TARGET = ALVOS[0]
        # Para mudar o alvo, basta editar este dicionário. Exemplo:
        # TARGET = {'mid': 3032, 'vote': 'up', 'slug': 'pearl_jam'}
        
        
        # --- CONFIGURAÇÕES DA REQUISIÇÃO (definidas apenas uma vez) ---
        URL = 'https://hentai2read.com/api'
        
        # Cookies podem ser definidos aqui se necessário
        COOKIES = {}
        
        def make_request(worker_id, target_info):
            """
            Função executada por cada thread. Envia uma requisição POST para o alvo definido.
            """
            # Monta o corpo (payload) da requisição com base nas informações do alvo
        
            HEADERS = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'pt-BR,pt;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://hentai2read.com',
                'priority': 'u=1, i',
                'referer': f'https://hentai2read.com/{target_info["slug"]}/', # Referer dinâmico
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Chrome OS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
        
            data = {
                'controller': 'manga',
                'action': 'recommendation',
                'mid': str(target_info['mid']),
                'vote': target_info['vote'],
            }
        
            try:
                # tempo entre 15 e 15 segundos, 1 mais um random entre 0 e 5
                tempo = 0.1 + random.random()
                time.sleep(tempo)
                response = requests.post(URL, headers=HEADERS, cookies=COOKIES, data=data)
                response.raise_for_status()  # Levanta um erro para status HTTP 4xx ou 5xx
        
                # Tenta decodificar a resposta como JSON
                try:
                    response_data = response.json()
                    if worker_id %100 == 0:
                        pass
                        # print(f"[Thread {worker_id}] Sucesso! MID: {target_info['mid']}, Voto: {target_info['vote']}, Status: {response.status_code}, Resposta: {response_data}")
                        # print(f"[Thread {worker_id}] Sucesso! MID: {target_info['mid']}, Voto: {target_info['vote']}, Status: {response.status_code}, Resposta: {response_data}")
                except ValueError:
                    # print(f"[Thread {worker_id}] Sucesso, mas resposta não é JSON! MID: {target_info['mid']}, Status: {response.status_code}, Resposta: {response.text}")
                    pass
        
        
                return f"MID {target_info['mid']} - Sucesso"
        
            except requests.exceptions.HTTPError as e:
                pass
                # print(f"[Thread {worker_id}] Erro HTTP! MID: {target_info['mid']}, Status: {e.response.status_code}, Resposta: {e.response.text}")
            except requests.exceptions.RequestException as e:
                # print(f"[Thread {worker_id}] ERRO na requisição! MID: {target_info['mid']}, Erro: {e}")
                pass
            return f"MID {target_info['mid']} - Erro"
        
        # --- EXECUÇÃO PRINCIPAL ---
        # if __name__ == "__main__":
        global alvo_atual
        # while True:
        #     # repetir smpte e exeutr s 6 e s 18h e minuto for 10
        #     if hora_atual := __import__('datetime').datetime.now().hour in [6, 13, 19, 22]:
        #         if __import__('datetime').datetime.now().minute == 28:
        #             # pervrre todos os alvos
        for alvo_atual2 in ALVOS:
            alvo_atual = alvo_atual2
            print(f"Iniciando {TOTAL_REQUESTS} requisições para o MID {alvo_atual['mid']} usando {NUM_THREADS} threads simultâneas...")
            UPS_VARIAVEIS = int(random.random()*MULTIPLIER)
            if alvo_atual['mid'] in EXTRA_UP:
                UPS_VARIAVEIS += MULTIPLIER
                if UPS_VARIAVEIS < 10000:
                    UPS_VARIAVEIS += MULTIPLIER
            if alvo_atual['mid'] in EXTRA_UP2:
                UPS_VARIAVEIS += MULTIPLIER
                if UPS_VARIAVEIS < 25000:
                    UPS_VARIAVEIS += MULTIPLIER*4
            if alvo_atual['mid'] in EXTRA_PLUS:
                UPS_VARIAVEIS += MULTIPLIER
                if UPS_VARIAVEIS < 25000:
                    UPS_VARIAVEIS += 25000
            print(f"Likes variaveis para o alvo {alvo_atual["slug"]}: {UPS_VARIAVEIS}")
            # Usa ThreadPoolExecutor para gerenciar um pool de threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                # Agenda a execução da função 'make_request' por 'TOTAL_REQUESTS' vezes.
                # O executor gerencia a fila, garantindo que no máximo 'NUM_THREADS'
                # sejam executadas ao mesmo tempo.
                futures = [executor.submit(make_request, i + 1, alvo_atual) for i in range(TOTAL_REQUESTS + UPS_VARIAVEIS)]
    
                # O bloco 'with' garante que o programa só continuará após
                # todas as 'TOTAL_REQUESTS' tarefas agendadas terminarem.
                concurrent.futures.wait(futures)
    
            print(f"Processo finalizado. {TOTAL_REQUESTS + UPS_VARIAVEIS} requisições foram enviadas.")
            time.sleep(2)
