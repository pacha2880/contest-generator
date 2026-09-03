import json
import random
import re
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Existing problems — URLs extracted from sheet, names/tags from CF API ──────
def e(rating, url, tema, obs, contest):
    return {"rating": rating, "url": url, "tema": tema, "obs": obs, "contest": contest}

EXISTING = {
    1: [
        e(2000,"https://codeforces.com/contest/852/problem/B",
          "DP / Matrices",
          "DP sobre la red neuronal; cuenta caminos usando multiplicación de matrices para estados grandes",
          "Bubble Cup X - Finals [Online Mirror]"),
        e(2200,"https://codeforces.com/contest/852/problem/F",
          "Combinatoria / Matemáticas",
          "Cuenta inversiones en la secuencia de productos; usa combinatoria para calcular el resultado final",
          "Bubble Cup X - Finals [Online Mirror]"),
        e(2200,"https://codeforces.com/contest/616/problem/E",
          "Matemáticas / Teoría de números",
          "sum(n mod k) = n*m - sum(floor(n/k)*k); calcula con fórmula cerrada en O(sqrt(n))",
          "Educational Codeforces Round 5"),
        e(1900,"https://codeforces.com/contest/622/problem/D",
          "Constructivo",
          "Coloca n en pos 1 y 1 en pos n+1; completa greedy para que ningún par a[i]+a[i+k] = n+1",
          "Educational Codeforces Round 7"),
    ],
    2: [
        e(1700,"https://codeforces.com/contest/852/problem/G",
          "Implementación",
          "Simula el terminal paso a paso; procesa cada comando en orden siguiendo las reglas del enunciado",
          "Bubble Cup X - Finals [Online Mirror]"),
        e(2100,"https://codeforces.com/contest/852/problem/D",
          "Búsqueda binaria / Flujos",
          "Binary search en la respuesta; verifica con matching/flujo máximo si es alcanzable",
          "Bubble Cup X - Finals [Online Mirror]"),
        e(2100,"https://codeforces.com/contest/852/problem/E",
          "Programación dinámica",
          "DP con estados de decisión en cada casino; optimiza transiciones evitando recálculos",
          "Bubble Cup X - Finals [Online Mirror]"),
        e(2200,"https://codeforces.com/contest/612/problem/E",
          "Constructivo / Ciclos",
          "Halla p tal que p∘p = permutación dada; usa estructura de ciclos: ciclos pares se parten, impares se fusionan",
          "Educational Codeforces Round 4"),
    ],
    3: [
        e(2000,"https://codeforces.com/contest/598/problem/E",
          "DP / Fuerza bruta",
          "DP sobre trozos de chocolate; optimiza con sumas de prefijo para evitar recálculo en cada ruptura",
          "Educational Codeforces Round 1"),
        e(2900,"https://codeforces.com/contest/598/problem/F",
          "Geometría",
          "Calcula la longitud promedio de corte con integración geométrica; descompone la integral por segmentos",
          "Educational Codeforces Round 1"),
        e(2600,"https://codeforces.com/contest/622/problem/F",
          "Matemáticas / Interpolación",
          "Usa interpolación de Lagrange con O(k) puntos para hallar la fórmula de suma de k-ésimas potencias",
          "Educational Codeforces Round 7"),
    ],
    4: [
        e(2800,"https://codeforces.com/contest/600/problem/F",
          "Grafos / Coloreo de aristas",
          "Teorema de Vizing: grafos bipartitos se colorean con Δ colores; usa flujo máximo para asignarlo",
          "Educational Codeforces Round 2"),
        e(2000,"https://codeforces.com/contest/609/problem/D",
          "Búsqueda binaria / Greedy",
          "Binary search en el presupuesto máximo; compra los k artículos más baratos de cada tienda greedy",
          "Educational Codeforces Round 3"),
        e(2200,"https://codeforces.com/contest/622/problem/E",
          "DFS / Greedy / Árboles",
          "DFS; para cada hoja programa su salida greedy evitando colisiones con el ancestro más cercano",
          "Educational Codeforces Round 7"),
    ],
    5: [
        e(2500,"https://codeforces.com/contest/609/problem/F",
          "Estructuras de datos / Greedy",
          "Asigna mosquitos a ranas con segment tree; la rana come si su lengua ≥ tamaño; cola de espera para el resto",
          "Educational Codeforces Round 3"),
        e(1800,"https://codeforces.com/contest/612/problem/D",
          "Greedy / Ordenamiento",
          "Ordena eventos de inicio y fin; sweep line contando cuántos segmentos cubren cada punto",
          "Educational Codeforces Round 4"),
        e(2200,"https://codeforces.com/contest/620/problem/D",
          "Búsqueda binaria / Dos punteros",
          "Ordena cada mitad del arreglo; para cada elemento de la primera busca el complemento en la segunda con binary search",
          "Educational Codeforces Round 6"),
        e(2100,"https://codeforces.com/contest/632/problem/D",
          "Fuerza bruta / Matemáticas",
          "Para cada diferencia d posible busca la PA más larga; itera sobre d en O(max_val) total",
          "Educational Codeforces Round 9"),
    ],
}

# ── 50 new problems — 10 per contest ─────────────────────────────────────────
# Distribution per contest: 2×1900, 1×1800, 2×1700, 2×1300, 2×900, 1×800
def p(rating, name, cid, idx, tema, obs, contest):
    return {
        "rating":  rating,
        "name":    name,
        "url":     f"https://codeforces.com/contest/{cid}/problem/{idx}",
        "tema":    tema,
        "obs":     obs,
        "contest": contest,
    }

NEW = {
    1: [
        p(1900,"Flip the Bit (Hard Version)",      2217,"D",  "Divide y vencerás",          "Divide el array a la mitad; combina resultados de subsegmentos con flips acumulados en cada nivel","Codeforces Round 1091 (Div. 2) and CodeCraft 26"),
        p(1900,"Sub-RBS (Hard Version)",           2190,"B2", "Programación dinámica",       "Para cada posición derecha rastrea el balance mínimo; usa mapa de frecuencias de prefijos","Codeforces Round 1073 (Div. 1)"),
        p(1800,"Interactive Graph (Simple Ver.)",  2196,"C1", "Grafos / Interactivo",        "Haz consultas para detectar el grado de cada nodo; búsqueda binaria sobre el grafo","Codeforces Round 1079 (Div. 1)"),
        p(1700,"Interval Mod",                     2215,"A",  "Búsqueda binaria / Matemáticas","Búsqueda binaria sobre r; verifica si existe k tal que k·d cae en [l, r]","Codeforces Round 1092 (THUPC 2026)"),
        p(1700,"For the Champion",                 2135,"B",  "Constructivo / Greedy",       "El campeón debe ganar a todos; si el máximo es único puede ir en cualquier lugar, si hay empate verifica adyacencia","Codeforces Round 1046 (Div. 1)"),
        p(1300,"THU Packing Puzzle",               2216,"B",  "Constructivo / Greedy",       "Empaca piezas de mayor a menor; verifica si caben en las filas disponibles sin solapar","Codeforces Round 1092 (THUPC 2026)"),
        p(1300,"Restricted Sorting",               2187,"A",  "Greedy / Ordenamiento",       "Si el intervalo restringido cubre todos los elementos fuera de su posición final, el sort es posible","Codeforces Round 1077 (Div. 1)"),
        p(900, "Course Wishes",                    2216,"A",  "Greedy / Matemáticas",        "Cuenta slots disponibles vs deseos; compara directamente — si hay más slots que deseos siempre se puede","Codeforces Round 1092 (THUPC 2026)"),
        p(900, "XOR = Average",                    1758,"B",  "Constructivo / Matemáticas",  "Si n es impar siempre hay construcción válida; si n es par todos los elementos deben ser iguales","Codeforces Round 836 (Div. 2)"),
        p(800, "LOL Lovers",                       1912,"L",  "Constructivo / Cadenas",      "Necesitas ceil(n/3)·2 letras L y floor(n/3) letras O; construye LOLLOL... y recorta","ICPC NERC 2023-2024 Mirror"),
    ],
    2: [
        p(1900,"Little String (Easy Version)",     2189,"D1", "Constructivo / Greedy",       "Asigna el menor carácter disponible a cada posición en orden; verifica que no colisione con restricciones","Codeforces Round 1075 (Div. 2)"),
        p(1900,"Nastiness of Segments",            2184,"G",  "Greedy / Sweep line",         "Ordena eventos de inicio/fin; con sweep line cuenta pares de segmentos que no pueden coexistir","Codeforces Round 1072 (Div. 3)"),
        p(1800,"Shortest Statement Ever",          2187,"B",  "Constructivo / Greedy",       "Construye la cadena de longitud mínima que satisface todas las condiciones de substring simultáneamente","Codeforces Round 1077 (Div. 1)"),
        p(1700,"Arithmetics Competition",          2132,"E",  "Constructivo / Matemáticas",  "Construye la progresión aritmética que maximiza/minimiza el resultado; verifica divisibilidad","Codeforces Round 1043 (Div. 3)"),
        p(1700,"Minimize Fixed Points",            2123,"F",  "Constructivo / Greedy",       "Itera por la permutación; desplaza elementos en ciclos para eliminar puntos fijos con shifts cíclicos mínimos","Codeforces Round 1034 (Div. 3)"),
        p(1300,"Cyclic Merging",                   2165,"A",  "Constructivo / Greedy",       "Fusionar dos ciclos adyacentes elimina un ciclo; la respuesta es el número de ciclos iniciales menos 1","Codeforces Round 1064 (Div. 1)"),
        p(1300,"Incremental Path",                 2150,"A",  "Greedy / Grafos",             "Extiende el camino tomando siempre la arista de mayor peso disponible sin repetir nodo","Codeforces Round 1053 (Div. 1)"),
        p(900, "Array Eversion",                   1585,"B",  "Greedy / Observación",        "Cuenta cuántas veces el sufijo máximo cambia de posición al recorrer de derecha a izquierda; eso más 1 es la respuesta","Technocup 2022 - Elimination Round 3"),
        p(900, "Luntik and Subsequences",          1582,"B",  "Combinatoria",                "Los ceros son los únicos candidatos; con k ceros la respuesta es k·2^(k-1) — suma de tamaños de subconjuntos que incluyen al menos un 0","Codeforces Round 750 (Div. 2)"),
        p(800, "Increasing and Decreasing",        1864,"A",  "Constructivo",                "Pon 1 al inicio y n al final; los elementos del medio se colocan para cumplir ambas condiciones fácilmente","Harbour.Space Scholarship Contest 2023-2024"),
    ],
    3: [
        p(1900,"Wishing Cards",                    2174,"B",  "Constructivo",                "Verifica paridad de la suma total; construye la asignación greedy con intercambios controlados","Codeforces Round 1069 (Div. 1)"),
        p(1900,"Antiamuny Wants to Learn Swap",    2138,"B",  "Constructivo / Greedy",       "Rastrea posiciones requeridas de cada elemento; cuenta cuántos intercambios son ineludibles con estructura de seguimiento","Codeforces Round 1048 (Div. 1)"),
        p(1800,"Mixing MEXes",                     2185,"G",  "Greedy / Matemáticas",        "Para cada posición calcula su contribución al MEX global; procesa de mayor a menor con estructura auxiliar","Codeforces Round 1074 (Div. 4)"),
        p(1700,"Manhattan Pairs",                  2122,"C",  "Matemáticas / Geometría",     "Rota coordenadas 45°; en el sistema rotado la distancia Manhattan se convierte en norma infinito","Order Capital Round 1 (Div. 1 + Div. 2)"),
        p(1700,"Dining Hall",                      2090,"C",  "Greedy / Implementación",     "Procesa peticiones en orden cronológico; asigna el asiento disponible más cercano a la posición pedida","Codeforces Round 1012 (Div. 2)"),
        p(1300,"Kar Salesman",                     2022,"B",  "Greedy / Matemáticas",        "La respuesta es max(suma de valores positivos, valor máximo); el vendedor siempre puede cubrir el máximo elemento","Codeforces Round 978 (Div. 2)"),
        p(1300,"Manhattan Permutations",           1978,"C",  "Constructivo / Greedy",       "Intercambia elementos adyacentes greedy; cada swap suma exactamente 1 a la distancia Manhattan total","Codeforces Round 953 (Div. 2)"),
        p(900, "Napoleon Cake",                    1501,"B",  "Prefijos / Implementación",   "Para cada ingrediente marca el rango de capas que influye; usa diferencias de array para actualizar en O(n)","Codeforces Round 707 (Div. 2)"),
        p(900, "From Zero To Y",                   1488,"A",  "Matemáticas",                 "Calcula el máximo Y alcanzable desde 0 con las operaciones dadas; verifica si Y es múltiplo de lo acumulable","Kotlin Heroes: Episode 6"),
        p(800, "Candies",                          1810,"B",  "Matemáticas",                 "La suma total de caramelos debe ser par para dividirlos en dos mitades iguales; verificación directa","CodeTON Round 4 (Div. 1 + Div. 2)"),
    ],
    4: [
        p(1900,"Omg Graph",                        2117,"G",  "Grafos / Greedy",             "Construye el grafo con estructura especial; BFS/DFS desde el nodo más conectado para maximizar la respuesta","Codeforces Round 1029 (Div. 3)"),
        p(1900,"D/D/D",                            2109,"D",  "Constructivo / Matemáticas",  "Construye la secuencia donde cada elemento divide al siguiente; nota que basta con dos valores distintos","Codeforces Round 1025 (Div. 2)"),
        p(1800,"Not Alone",                        2153,"D",  "Greedy / Ordenamiento",       "Ordena el arreglo; verifica si un único elemento puede dominar todos los demás según la condición","Codeforces Round 1057 (Div. 2)"),
        p(1700,"Simple Permutation",               2089,"A",  "Constructivo / Matemáticas",  "Construye la permutación tal que p[p[i]]≠i para todo i; alterna bloques de 3 elementos","Codeforces Round 1012 (Div. 1)"),
        p(1700,"Best Runner",                      2080,"B",  "Matemáticas / Greedy",        "Calcula cuántos segmentos puede ganar cada corredor; el ganador es quien acumule más tramos con su velocidad","XIX Open Olympiad in Informatics - Day 2"),
        p(1300,"Подкрутка II (Twitch II)",         1769,"C2", "Búsqueda binaria / Greedy",   "Binary search en el número de turnos; simula hacia adelante para verificar si es factible en ≤ mid pasos","VK Cup 2022 - Квалификация"),
        p(1300,"Directional Increase",             1693,"A",  "Constructivo / Greedy",       "El mayor elemento define la dirección de expansión; coloca el resto en orden creciente hacia el lado del máximo","Codeforces Round 800 (Div. 1)"),
        p(900, "Waste Sorting",                    1468,"N",  "Greedy / Implementación",     "Ordena basura por tipo; llena los contenedores de mayor a menor capacidad verificando que cada uno quepa","ICPC NERC 2020-2021 Southern Volga Mirror"),
        p(900, "Elimination",                      1445,"B",  "Matemáticas",                 "En cada ronda se elimina la mitad; el número total de victorias del campeón es siempre ceil(log2(n))","Codeforces Round 680 (Div. 2)"),
        p(800, "Узкая дорога (Narrow Road)",       1769,"A",  "Implementación",              "Simula encuentros en la carretera estrecha; cada cruce agrega el tiempo de espera entre las personas","VK Cup 2022 - Квалификация"),
    ],
    5: [
        p(1900,"Finding OR Sum",                   2077,"B",  "Bits / Matemáticas",          "Para cada bit analiza si puede aparecer en algún OR de subconjunto; suma las contribuciones bit a bit","Codeforces Round 1008 (Div. 1)"),
        p(1900,"Mascot Naming",                    2068,"F",  "Constructivo / Cadenas",      "Genera nombres greedy verificando unicidad con un conjunto; el número de nombres posibles crece factorialmente","European Championship 2025 Mirror"),
        p(1800,"Inversion Value of a Permutation", 2145,"D",  "Inversiones / BIT",           "Cuenta inversiones con BIT/merge sort; el valor de inversión de posición i es el número de j<i con p[j]>p[i]","Educational Codeforces Round 183 (Div. 2)"),
        p(1700,"Goodbye, Banker Life",             2072,"F",  "Grafos / Greedy",             "Modela como grafo bipartito; asigna trabajadores a bancos con matching greedy por prioridad de salario","Codeforces Round 1006 (Div. 3)"),
        p(1700,"Skibidus and Capping",             2065,"G",  "Constructivo / Greedy",       "Determina qué valores sobreviven el capping; greedy de izquierda a derecha manteniendo el máximo actual","Codeforces Round 1003 (Div. 4)"),
        p(1300,"Make it Increasing",               1667,"A",  "Constructivo / Matemáticas",  "Solo puedes sumar C a un prefijo una vez; prueba cada posición de corte y verifica si el resultado es estrictamente creciente","Codeforces Round 783 (Div. 1)"),
        p(1300,"And It's Non-Zero",                1615,"B",  "Bits / Matemáticas",          "Para cada bit cuenta cuántos números en [l,r] lo tienen en 1; si algún bit aparece en todos, el AND es no-cero","Codeforces Global Round 18"),
        p(900, "Balls of Buma",                    1267,"B",  "Constructivo / Simulación",   "Simula la captura de bolas por colores; el jugador con más bolas del color mayoritario captura a todos","ICPC NERC 2019-2020 Finals Mirror"),
        p(900, "Forgetting Things",                1225,"A",  "Constructivo",                "La primera página del capítulo actual debe ser exactamente el sucesor del último capítulo; verifica el rango","Technocup 2020 - Elimination Round 2"),
        p(800, "Immobile Knight",                  1739,"A",  "Matemáticas",                 "El caballo no puede moverse solo en tableros muy pequeños (n=1 o m=1 o n=m=2); verifica esas condiciones","Educational Codeforces Round 136 (Div. 2)"),
    ],
}


def build_contest_data():
    """Combine existing + new problems, shuffle each contest."""
    result = {}
    for c in range(1, 6):
        probs = []
        for ex in EXISTING[c]:
            probs.append({
                "rating":  ex["rating"],
                "display": ex.get("url", ""),   # now we have the URL
                "tema":    ex["tema"],
                "obs":     ex["obs"],
                "contest": ex["contest"],
            })
        for nw in NEW[c]:
            probs.append({
                "rating":  nw["rating"],
                "display": nw["url"],
                "tema":    nw["tema"],
                "obs":     nw["obs"],
                "contest": nw["contest"],
            })
        random.shuffle(probs)
        result[c] = probs
    return result


def build_sheet_rows(contest_data):
    """Build the full 2D list of rows for the sheet."""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    rows = []
    for c in range(1, 6):
        probs = contest_data[c]
        n = len(probs)

        # Header: "A - #2217D" linked to CF problem, plain letter if no URL
        header = [f"Contest {c}"]
        for i, prob in enumerate(probs):
            letter = letters[i]
            url = prob.get("display", "")
            if url:
                cf = re.search(r"/contest/(\d+)/problem/([A-Z0-9]+)", url, re.I)
                label = f"{letter} - #{cf.group(1)}{cf.group(2)}" if cf else letter
                header.append(f'=HYPERLINK("{url}","{label}")')
            else:
                header.append(letter)

        rating  = ["rating"]      + [str(p["rating"])  for p in probs]
        tema    = ["tema"]        + [p["tema"]          for p in probs]
        obs     = ["observación"] + [p["obs"]           for p in probs]
        contest = ["contest"]     + [p["contest"]       for p in probs]
        blank   = [""] * (n + 1)

        rows += [header, rating, tema, obs, contest, blank]
    return rows


def upload(rows, sheets_url, creds_file):
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(sheets_url)
    ws = sh.sheet1
    ws.clear()
    ws.update(rows, value_input_option="USER_ENTERED")
    print(f"Sheet updated: {len(rows)} rows written.")


def main():
    with open("config.json") as f:
        cfg = json.load(f)
    sheets_url = cfg.get("sheets_url", "")
    creds_file = cfg.get("credentials_file", "credentials.json")

    if not sheets_url:
        print("No sheets_url in config.json")
        return
    if not os.path.exists(creds_file):
        print(f"Missing {creds_file}")
        return

    random.seed(42)  # reproducible shuffle — remove for true random each run
    contest_data = build_contest_data()
    rows = build_sheet_rows(contest_data)

    print("Preview (first contest):")
    for r in rows[:6]:
        print(r)
    print(f"\nTotal rows: {len(rows)}")

    upload(rows, sheets_url, creds_file)


if __name__ == "__main__":
    main()
