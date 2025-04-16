import json
import re
import os

def main():
    """
    Ez a szkript egy javított megközelítést használ a problémás JSON javítására.
    A cél, hogy megőrizzük az eredeti test.json fájl összes adatát, miközben kijavítjuk
    a hibás JSON formátumot a response mezőben.
    """
    # Beolvassuk az eredeti JSON fájlt
    with open('test.json', 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            print("Eredeti JSON sikeresen beolvasva.")
        except json.JSONDecodeError as e:
            print(f"Hiba az eredeti JSON beolvasásakor: {e}")
            return
    
    # Ellenőrizzük, hogy a response mező string-e
    if "response" in data and isinstance(data["response"], str):
        print("A 'response' mezőben string formátumú JSON található, megpróbáljuk kijavítani...")
        response_str = data["response"]
        
        # 1. lépés: A stringet tisztítjuk az escape-elt karakterektől
        # Az \n karaktereket megtartjuk (könnyebb olvasni)
        cleaned_str = response_str
        
        # 2. lépés: A "félelmetes tempó" kifejezés környékén lévő problémát javítjuk
        # Keressük meg a problémás mintát
        problem_pattern = r'(angot a ")félelmetes tempó(" említésekor)'
        if re.search(problem_pattern, cleaned_str):
            print("Megtaláltuk a problémás 'félelmetes tempó' kifejezést, javítjuk...")
            # Vesszőt adunk a problémás rész elé
            cleaned_str = re.sub(problem_pattern, r'\1", "félelmetes tempó\2', cleaned_str)
        
        # 3. lépés: Egyéb általános JSON hibák javítása
        # Dupla idézőjelek javítása
        cleaned_str = cleaned_str.replace('""', '","')
        
        # Hiányzó vesszők hozzáadása kulcs-érték párok között
        cleaned_str = re.sub(r'"}(\s*)"', r'"},\1"', cleaned_str)
        
        # Záró idézőjel utáni hiányzó vessző hozzáadása
        cleaned_str = re.sub(r'"(\s*)(?=\{)', r'",\1', cleaned_str)
        
        try:
            # Próbáljuk meg feldolgozni a javított JSON stringet
            response_obj = json.loads(cleaned_str)
            print("A javított response sikeres JSON objektum lett!")
            # Frissítsük az eredeti objektumot
            data["response"] = response_obj
        except json.JSONDecodeError as e:
            print(f"A javítás nem sikerült: {e}")
            
            # Még egy próbálkozás: használjuk a json_repair könyvtárat, ha elérhető
            try:
                from json_repair import repair_json
                print("Kísérlet a json_repair könyvtárral...")
                repaired = repair_json(cleaned_str)
                response_obj = json.loads(repaired)
                print("A json_repair könyvtárral sikeresen javítottuk a JSON-t!")
                data["response"] = response_obj
            except (ImportError, json.JSONDecodeError) as e2:
                print(f"A json_repair próbálkozás sem sikerült: {e2}")
                
                # Utolsó megoldásként próbáljuk meg manuálisan javítani a response stringet
                # A félelmetes tempó résznél fellépő hibát célzottan kezeljük
                print("Kézi javítás próbálása...")
                
                # A response stringet sorokra bontjuk
                lines = cleaned_str.split('\n')
                
                # Keressük meg azt a sort, ami tartalmazza a problémás kifejezést
                problematic_line_index = -1
                for i, line in enumerate(lines):
                    if "félelmetes tempó" in line:
                        problematic_line_index = i
                        break
                
                if problematic_line_index != -1:
                    # Javítsuk a problémás sort
                    original_line = lines[problematic_line_index]
                    print(f"Problémás sor: {original_line}")
                    
                    # Cseréljük ki a problémás részt
                    fixed_line = original_line.replace(
                        '"Használj erőteljesebb hangot a "félelmetes tempó" említésekor."', 
                        '"Használj erőteljesebb hangot a", "félelmetes tempó említésekor."'
                    )
                    
                    if fixed_line == original_line:
                        # Ha nem találta meg a pontos mintát, próbáljunk egy általánosabb helyettesítést
                        fixed_line = re.sub(
                            r'(.*"Használj erőteljesebb hangot a ")([^"]+)(" említésekor.".*)', 
                            r'\1", "\2\3', 
                            original_line
                        )
                    
                    lines[problematic_line_index] = fixed_line
                    print(f"Javított sor: {fixed_line}")
                    
                    # Állítsuk össze újra a stringet
                    cleaned_str = '\n'.join(lines)
                    
                    try:
                        response_obj = json.loads(cleaned_str)
                        print("A kézi javítás sikeres!")
                        data["response"] = response_obj
                    except json.JSONDecodeError as e3:
                        print(f"A kézi javítás sem sikerült: {e3}")
                        
                        # Utolsó próbálkozás: más megközelítés
                        # Próbáljuk meg külön-külön javítani a response objektumot
                        try:
                            # A response string első és utolsó karakterét (a külső kapcsos zárójeleket) elhagyjuk
                            inner_content = cleaned_str.strip()[1:-1].strip()
                            
                            # Manuálisan építjük fel a JSON objektumot
                            # Először kiszedjük a "video_elemzes" részt
                            match = re.search(r'"video_elemzes"\s*:\s*(\{[^}]*\})', inner_content, re.DOTALL)
                            if match:
                                video_elemzes_str = match.group(1)
                                # Próbáljuk meg javítani csak ezt a részt
                                try:
                                    temp_json = f'{{"video_elemzes": {video_elemzes_str}}}'
                                    response_obj = json.loads(temp_json)
                                    print("Sikerült javítani a video_elemzes részét!")
                                    data["response"] = response_obj
                                except json.JSONDecodeError:
                                    # Ha ez sem segít, adjunk vissza egy alap struktúrát,
                                    # de megtartva annyit az eredetiből, amennyit csak lehet
                                    print("Visszaállunk egy alapértelmezett struktúrára, de megtartjuk az eredeti adatokat, ahol csak lehet")
                                    
                                    # Visszakapjuk az eredeti JSON fájl tartalmát
                                    with open('test.json', 'r', encoding='utf-8') as f:
                                        raw_content = f.read()
                                    
                                    # Egyszerű szöveghelyettesítés a problémás részre
                                    fixed_content = raw_content.replace(
                                        '"Használj erőteljesebb hangot a "félelmetes tempó" említésekor."',
                                        '"Használj erőteljesebb hangot a \\"félelmetes tempó\\" említésekor."'
                                    )
                                    
                                    try:
                                        # Próbáljuk meg újra betölteni
                                        temp_data = json.loads(fixed_content)
                                        
                                        # Ha sikerült, próbáljuk meg újra a response mezőt feldolgozni
                                        if isinstance(temp_data.get("response"), str):
                                            try:
                                                temp_response = json.loads(temp_data["response"])
                                                data["response"] = temp_response
                                                print("Sikerült javítani az eredeti JSON-t egyszerű szöveghelyettesítéssel!")
                                            except:
                                                print("Nem sikerült a response mezőt feldolgozni")
                                    except:
                                        print("A szöveg helyettesítés sem segített")
                        except Exception as e4:
                            print(f"Az utolsó próbálkozás is sikertelen: {e4}")
    
    # Mentsük el a javított JSON-t
    with open('better_fixed.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print("Javított JSON elmentve: better_fixed.json")
    
    # Ellenőrizzük, hogy a response mező objektum-e most már
    if isinstance(data.get("response"), dict):
        print("A JSON sikeres: a response mező most már objektum!")
        
        # Nézzük meg, mennyi adatot sikerült megőriznünk
        if "video_elemzes" in data["response"]:
            metadata = data["response"]["video_elemzes"].get("metadata", {})
            intervallumok = data["response"]["video_elemzes"].get("intervallumok", [])
            print(f"Megőrzött adatok: video_hossz={metadata.get('video_hossz', 'N/A')}, intervallumok száma={len(intervallumok)}")
    else:
        print("A response mező még mindig nem objektum!")

if __name__ == "__main__":
    main()
