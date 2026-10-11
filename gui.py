"""
gui.py
Esqueleto de GUI de escritorio para ProblemsHunter (FreeSimpleGUI).

Solo estructura por ahora: una pestaña por flujo (Codeforces, AtCoder, Gym)
con los campos de config.json precargados, y un log compartido abajo. Los
botones "Generar" todavia no estan conectados al backend — eso necesita
correr cada flujo en un hilo aparte (para no congelar la ventana durante
los 15s-2min que tardan) y pasarle on_progress=<algo que escriba en -LOG->
en vez de on_progress=print.
"""

import json

import FreeSimpleGUI as sg

CONFIG_PATH = "config.json"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def csv_field(values):
    return ", ".join(str(v) for v in values)


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


def main():
    cfg = load_config()

    tabs = sg.TabGroup([[codeforces_tab(cfg), atcoder_tab(cfg), gym_tab(cfg)]])
    layout = [
        [tabs],
        [sg.Multiline(size=(90, 15), key="-LOG-", autoscroll=True, disabled=True)],
    ]
    window = sg.Window("ProblemsHunter", layout, finalize=True)

    run_buttons = {"-CF-RUN-", "-AC-RUN-", "-GYM-RUN-"}

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in run_buttons:
            # TODO: leer los campos del tab correspondiente, correr el
            # flujo real (app.main()/atcoder.find_recommended_abc()/
            # gym.find_untouched_gyms()+select_recommendations()) en un
            # hilo aparte, con on_progress=<callback que escriba en -LOG->
            # via una queue.Queue (ver nota del docstring).
            window["-LOG-"].print(f"[{event}] todavia no conectado al backend (esqueleto).")

    window.close()


if __name__ == "__main__":
    main()
