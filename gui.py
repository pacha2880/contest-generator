"""
gui.py
GUI de escritorio para ProblemsHunter (FreeSimpleGUI).

Cada pestana (Codeforces/AtCoder/Gym) edita su parte de config.json. Al
apretar "Generar":
  1. Se relee config.json del disco (por si cambio desde afuera).
  2. Se actualiza solo el bloque de ese flujo con los valores del formulario
     y se guarda — asi la consola (`py main.py <flujo>`) ve los mismos
     cambios despues. Si algun campo no parsea (ej. "Count" no numerico),
     no se guarda nada y se reporta el error.
  3. Se corre el mismo app.main()/atcoder.main()/gym.main() que usa la
     consola, pasandole on_progress=<callback propio> en vez de print —
     misma logica, mismos archivos de salida, sin codigo duplicado.
  4. Esa corrida va en un hilo aparte (los fetches tardan 15s-2min) para no
     congelar la ventana. El callback usa window.write_event_value(), que es
     thread-safe, en vez de tocar el widget del log directo desde el hilo.

Los 3 botones "Generar" se deshabilitan mientras cualquiera de los 3 esta
corriendo, para no pisarse escribiendo config.json al mismo tiempo.
"""

import json
import threading

import FreeSimpleGUI as sg

import app
import atcoder
import gym
from cancel import StoppedByUser

CONFIG_PATH = "config.json"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
        f.write("\n")


def csv_field(values):
    return ", ".join(str(v) for v in values)


def parse_csv(text):
    return [v.strip() for v in text.split(",") if v.strip()]


def parse_int(text, field_name):
    text = text.strip()
    if not text:
        raise ValueError(f"'{field_name}' no puede estar vacío")
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"'{field_name}' debe ser un número entero, no {text!r}")


def parse_optional_int(text, field_name):
    text = text.strip()
    return parse_int(text, field_name) if text else None


def codeforces_tab(cfg):
    cf_cfg = cfg.get("codeforces", {})
    layout = [
        [sg.Text("Users", size=(16, 1)), sg.Input(csv_field(cf_cfg.get("users", [])), key="-CF-USERS-")],
        [sg.Text("Difficulties", size=(16, 1)), sg.Input(csv_field(cf_cfg.get("difficulties", [])), key="-CF-DIFFICULTIES-")],
        [sg.Text("Output file", size=(16, 1)), sg.Input(cf_cfg.get("output_links", "results.txt"), key="-CF-OUTPUT-")],
        [sg.Button("Generar", key="-CF-RUN-")],
    ]
    return sg.Tab("Codeforces", layout)


def atcoder_tab(cfg):
    ac_cfg = cfg.get("atcoder", {})
    layout = [
        [sg.Text("Users (AtCoder)", size=(16, 1)), sg.Input(csv_field(ac_cfg.get("users_atcoder", [])), key="-AC-USERS-")],
        [sg.Text("Users (vjudge)", size=(16, 1)), sg.Input(csv_field(ac_cfg.get("users_vjudge", [])), key="-AC-VJUDGE-")],
        [sg.Text("Count", size=(16, 1)), sg.Input(str(ac_cfg.get("count", 5)), key="-AC-COUNT-")],
        [sg.Text("Lookback", size=(16, 1)), sg.Input(str(ac_cfg.get("lookback", 50)), key="-AC-LOOKBACK-")],
        [sg.Text("Problems", size=(16, 1)), sg.Input(csv_field(ac_cfg.get("problems", [])), key="-AC-PROBLEMS-")],
        [sg.Text("Output file", size=(16, 1)), sg.Input(ac_cfg.get("output_links", "outputs/atcoder_links.txt"), key="-AC-OUTPUT-")],
        [sg.Button("Generar", key="-AC-RUN-")],
    ]
    return sg.Tab("AtCoder", layout)


def gym_tab(cfg):
    gym_cfg = cfg.get("gym", {})
    filters = gym_cfg.get("filters", {})
    layout = [
        [sg.Text("Users", size=(16, 1)), sg.Input(csv_field(gym_cfg.get("users", [])), key="-GYM-USERS-")],
        [sg.Text("Count", size=(16, 1)), sg.Input(str(gym_cfg.get("count", 10)), key="-GYM-COUNT-")],
        [sg.Checkbox("Require editorial", default=gym_cfg.get("require_editorial", False), key="-GYM-REQEDIT-")],
        [sg.Text("Difficulty min/max", size=(16, 1)),
         sg.Input(str(filters.get("difficulty_min", "")), size=(5, 1), key="-GYM-DIFFMIN-"),
         sg.Input(str(filters.get("difficulty_max", "")), size=(5, 1), key="-GYM-DIFFMAX-")],
        [sg.Text("Output CSV", size=(16, 1)), sg.Input(gym_cfg.get("output_csv", "outputs/gym_recommendations.csv"), key="-GYM-OUTPUT-")],
        [sg.Button("Generar", key="-GYM-RUN-")],
    ]
    return sg.Tab("Gym", layout)


def run_codeforces(values, on_progress, should_stop):
    cfg = load_config()
    cf_cfg = cfg.setdefault("codeforces", {})
    cf_cfg["users"] = parse_csv(values["-CF-USERS-"])
    cf_cfg["difficulties"] = parse_csv(values["-CF-DIFFICULTIES-"])
    cf_cfg["output_links"] = values["-CF-OUTPUT-"].strip() or "results.txt"
    save_config(cfg)
    app.main(on_progress=on_progress, should_stop=should_stop)


def run_atcoder(values, on_progress, should_stop):
    cfg = load_config()
    ac_cfg = cfg.setdefault("atcoder", {})
    ac_cfg["users_atcoder"] = parse_csv(values["-AC-USERS-"])
    ac_cfg["users_vjudge"] = parse_csv(values["-AC-VJUDGE-"])
    ac_cfg["count"] = parse_int(values["-AC-COUNT-"], "Count")
    ac_cfg["lookback"] = parse_int(values["-AC-LOOKBACK-"], "Lookback")
    ac_cfg["problems"] = parse_csv(values["-AC-PROBLEMS-"])
    ac_cfg["output_links"] = values["-AC-OUTPUT-"].strip() or "outputs/atcoder_links.txt"
    save_config(cfg)
    atcoder.main(on_progress=on_progress, should_stop=should_stop)


def run_gym(values, on_progress, should_stop):
    cfg = load_config()
    gym_cfg = cfg.setdefault("gym", {})
    gym_cfg["users"] = parse_csv(values["-GYM-USERS-"])
    gym_cfg["count"] = parse_int(values["-GYM-COUNT-"], "Count")
    gym_cfg["require_editorial"] = bool(values["-GYM-REQEDIT-"])
    gym_cfg["output_csv"] = values["-GYM-OUTPUT-"].strip() or "outputs/gym_recommendations.csv"
    filters = gym_cfg.setdefault("filters", {})
    filters["difficulty_min"] = parse_optional_int(values["-GYM-DIFFMIN-"], "Difficulty min")
    filters["difficulty_max"] = parse_optional_int(values["-GYM-DIFFMAX-"], "Difficulty max")
    save_config(cfg)
    gym.main(on_progress=on_progress, should_stop=should_stop)


def main():
    cfg = load_config()

    tabs = sg.TabGroup([[codeforces_tab(cfg), atcoder_tab(cfg), gym_tab(cfg)]])
    layout = [
        [tabs],
        [sg.Button("Detener", key="-STOP-", disabled=True), sg.Button("Limpiar", key="-CLEAR-")],
        [sg.Multiline(size=(90, 15), key="-LOG-", autoscroll=True, disabled=True)],
    ]
    window = sg.Window("ProblemsHunter", layout, finalize=True)

    run_buttons = {"-CF-RUN-": ("Codeforces", run_codeforces),
                   "-AC-RUN-": ("AtCoder", run_atcoder),
                   "-GYM-RUN-": ("Gym", run_gym)}
    running = False
    stop_event = threading.Event()

    def log(msg):
        window["-LOG-"].print(msg)

    def on_progress(msg):
        window.write_event_value("-PROGRESS-", msg)

    def set_running(value):
        nonlocal running
        running = value
        for key in run_buttons:
            window[key].update(disabled=value)
        window["-STOP-"].update(disabled=not value)

    def worker(run_fn, values, label):
        try:
            run_fn(values, on_progress, stop_event.is_set)
            window.write_event_value("-DONE-", (label, "ok", None))
        except StoppedByUser:
            window.write_event_value("-DONE-", (label, "stopped", None))
        except Exception as e:
            window.write_event_value("-DONE-", (label, "error", str(e)))

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        if event in run_buttons and not running:
            stop_event.clear()
            set_running(True)
            label, run_fn = run_buttons[event]
            log(f"=== {label}: iniciando ===")
            threading.Thread(target=worker, args=(run_fn, values, label), daemon=True).start()

        elif event == "-STOP-" and running:
            stop_event.set()
            log("=== Deteniendo (puede tardar unos segundos en frenar) ===")

        elif event == "-CLEAR-":
            window["-LOG-"].update("")

        elif event == "-PROGRESS-":
            log(values[event])

        elif event == "-DONE-":
            label, status, error = values[event]
            if status == "ok":
                log(f"=== {label}: listo ===")
            elif status == "stopped":
                log(f"=== {label}: detenido por el usuario — no se generó ningún archivo ===")
            else:
                log(f"=== {label}: error — {error} ===")
            set_running(False)

    window.close()


if __name__ == "__main__":
    main()
