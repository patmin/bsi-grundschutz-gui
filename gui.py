from __future__ import annotations

import argparse
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

from ai_helper import AIHelpStore, ApiKeyStore, fetch_ai_help
from requirements_parser import Compendium, load_compendium
from status_store import StatusStore, VALID_STATUSES


class CompendiumApp(tk.Tk):
    def __init__(self, compendium: Compendium, store: StatusStore, api_key_store: ApiKeyStore, ai_help_store: AIHelpStore):
        super().__init__()
        self.title("IT-Grundschutz Kompendium - Statusuebersicht")
        self.geometry("1200x800")

        self.compendium = compendium
        self.store = store
        self.api_key_store = api_key_store
        self.ai_help_store = ai_help_store
        self.current_module = None
        self.current_requirements = []
        self.active_requirement = None
        self._is_fetching_help = False

        self._build_widgets()
        self._populate_modules()

    def _build_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        menubar = tk.Menu(self)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="OpenAI API-Key hinterlegen", command=self._prompt_api_key)
        menubar.add_cascade(label="Einstellungen", menu=settings_menu)
        self.config(menu=menubar)

        paned_main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned_main.grid(row=0, column=0, sticky="nsew")

        # Module List
        module_frame = ttk.Frame(paned_main, padding=10)
        paned_main.add(module_frame, weight=1)
        ttk.Label(module_frame, text="Bausteine").pack(anchor="w")
        self.module_list = tk.Listbox(module_frame, width=35, exportselection=False)
        self.module_list.pack(fill="both", expand=True)
        self.module_list.bind("<<ListboxSelect>>", self._on_module_select)

        # Right side with requirements and details
        right_container = ttk.Frame(paned_main, padding=10)
        right_container.columnconfigure(0, weight=1)
        right_container.rowconfigure(0, weight=1)
        paned_main.add(right_container, weight=4)

        paned_right = ttk.Panedwindow(right_container, orient=tk.VERTICAL)
        paned_right.grid(row=0, column=0, sticky="nsew")

        req_frame = ttk.Frame(paned_right)
        req_frame.columnconfigure(0, weight=1)
        paned_right.add(req_frame, weight=1)

        header_frame = ttk.Frame(req_frame)
        header_frame.grid(row=0, column=0, sticky="we")
        header_frame.columnconfigure(0, weight=1)
        ttk.Label(header_frame, text="Anforderungen").grid(row=0, column=0, sticky="w")

        self.status_filter = tk.StringVar(value="all")
        ttk.Label(header_frame, text="Statusfilter:").grid(row=0, column=1, sticky="e", padx=(10, 0))
        filter_values = ["all"] + VALID_STATUSES
        self.filter_menu = ttk.OptionMenu(
            header_frame,
            self.status_filter,
            "all",
            *filter_values,
            command=lambda *_: self._refresh_requirements(),
        )
        self.filter_menu.grid(row=0, column=2, sticky="e")

        self.requirements_list = tk.Listbox(req_frame, height=10, exportselection=False)
        self.requirements_list.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.requirements_list.bind("<<ListboxSelect>>", self._on_requirement_select)
        req_frame.rowconfigure(1, weight=1)

        detail_frame = ttk.Frame(paned_right, padding=(0, 5, 0, 0))
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(4, weight=1)
        paned_right.add(detail_frame, weight=3)

        self.detail_title = ttk.Label(detail_frame, text="Details", font=("Segoe UI", 12, "bold"))
        self.detail_title.grid(row=0, column=0, sticky="w")

        self.status_var = tk.StringVar(value="open")
        ttk.Label(detail_frame, text="Status").grid(row=1, column=0, sticky="w", pady=(5, 0))
        status_bar = ttk.Frame(detail_frame)
        status_bar.grid(row=1, column=0, sticky="we", pady=(5, 10))
        self.status_menu = ttk.OptionMenu(status_bar, self.status_var, "open", *VALID_STATUSES)
        self.status_menu.pack(side="left")
        ttk.Button(status_bar, text="Status speichern", command=self._save_status).pack(side="left", padx=10)

        ttk.Label(detail_frame, text="Notiz").grid(row=2, column=0, sticky="w")
        self.note_text = tk.Text(detail_frame, height=3)
        self.note_text.grid(row=2, column=0, sticky="we", pady=(0, 10))

        # Split description and hints vertically
        paned_detail = ttk.Panedwindow(detail_frame, orient=tk.VERTICAL)
        paned_detail.grid(row=4, column=0, sticky="nsew")

        desc_frame = ttk.Frame(paned_detail)
        desc_frame.columnconfigure(0, weight=1)
        ttk.Label(desc_frame, text="Beschreibung").grid(row=0, column=0, sticky="w")
        self.description_text = tk.Text(desc_frame, wrap="word", height=10)
        self.description_text.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        desc_frame.rowconfigure(1, weight=1)

        hints_frame = ttk.Frame(paned_detail)
        hints_frame.columnconfigure(0, weight=1)
        ttk.Label(hints_frame, text="KI Hilfe").grid(row=0, column=0, sticky="w")
        self.ai_help_text = tk.Text(hints_frame, wrap="word", height=8)
        self.ai_help_text.grid(row=1, column=0, sticky="nsew")
        self.ai_button = ttk.Button(hints_frame, text="Hilfe laden", command=self._request_ai_help)
        self.ai_button.grid(row=2, column=0, sticky="w", pady=(5, 0))
        hints_frame.rowconfigure(1, weight=1)

        paned_detail.add(desc_frame, weight=2)
        paned_detail.add(hints_frame, weight=1)

        for widget in [self.description_text, self.ai_help_text]:
            widget.configure(state="disabled")

    def _populate_modules(self) -> None:
        self.module_list.delete(0, tk.END)
        for module in self.compendium.modules.values():
            done = sum(1 for req in module.requirements if self.store.get_status(req.code) == "done")
            total = len(module.requirements)
            display = f"{module.code} ({done}/{total}) - {module.title}"
            self.module_list.insert(tk.END, display)

    def _on_module_select(self, event=None) -> None:
        selection = self.module_list.curselection()
        if not selection:
            return
        index = selection[0]
        module = list(self.compendium.modules.values())[index]
        self.current_module = module
        self._populate_requirements(module)

    def _refresh_requirements(self) -> None:
        self.requirements_list.delete(0, tk.END)
        if not self.current_module:
            return
        self.current_requirements = self.current_module.requirements
        selected_filter = self.status_filter.get()
        filtered_requirements = []
        for req in self.current_module.requirements:
            status = self.store.get_status(req.code) or "open"
            if selected_filter != "all" and status != selected_filter:
                continue
            filtered_requirements.append(req)
            display = f"{req.code} [{status}] {req.title}"
            self.requirements_list.insert(tk.END, display)
        self.current_requirements = filtered_requirements

        # wenn Filter greift und nichts uebrig bleibt -> Details zuruecksetzen
        if not filtered_requirements:
            self._clear_details()

    def _populate_requirements(self, module) -> None:
        self.current_requirements = module.requirements
        self._refresh_requirements()
        self._clear_details()

    def _on_requirement_select(self, event=None) -> None:
        selection = self.requirements_list.curselection()
        if not selection:
            return
        req = self.current_requirements[selection[0]]
        self._display_requirement(req)

    def _display_requirement(self, req) -> None:
        self.active_requirement = req
        self.detail_title.config(text=f"{req.code} - {req.title}")
        status_data = self.store.get(req.code) or {}
        status_val = status_data.get("status", "open")
        note_val = status_data.get("note", "")
        self.status_var.set(status_val)

        self.note_text.delete("1.0", tk.END)
        self.note_text.insert(tk.END, note_val)

        desc = req.description or "Keine Beschreibung gefunden."
        self._set_text(self.description_text, desc)
        help_text = self.ai_help_store.get_help(req.code)
        self._update_ai_text(help_text)
        self.ai_button.state(["!disabled"])

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, value)
        widget.configure(state="disabled")

    def _update_ai_text(self, value: Optional[str]) -> None:
        content = value if value else "Noch keine KI-Hilfe gespeichert. Nutzen Sie 'Hilfe laden'."
        self._set_text(self.ai_help_text, content)

    def _save_status(self) -> None:
        selection = self.requirements_list.curselection()
        if not selection:
            messagebox.showinfo("Hinweis", "Bitte waehlen Sie eine Anforderung aus.")
            return
        req = self.current_requirements[selection[0]]
        note_value = self.note_text.get("1.0", tk.END).strip()
        status = self.status_var.get()
        self.store.set_status(req.code, status, note_value)
        self.store.save()
        self._populate_modules()
        if self.current_module:
            self._refresh_requirements()
            if self.requirements_list.size() > 0:
                self.requirements_list.selection_set(min(selection[0], self.requirements_list.size() - 1))
        messagebox.showinfo("Gespeichert", f"Status fuer {req.code} gespeichert.")

    def _prompt_api_key(self) -> None:
        key = simpledialog.askstring("OpenAI API-Key", "Bitte API-Key eingeben (wird nur lokal gespeichert):", show='*')
        if key:
            self.api_key_store.save_key(key.strip())
            messagebox.showinfo("Gespeichert", "API-Key wurde hinterlegt.")

    def _request_ai_help(self) -> None:
        if not self.active_requirement:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Anforderung auswaehlen.")
            return
        api_key = self.api_key_store.load_key()
        if not api_key:
            messagebox.showwarning("API-Key fehlt", "Bitte ueber das Menue unter Einstellungen einen OpenAI API-Key speichern.")
            return
        if self._is_fetching_help:
            return
        self._is_fetching_help = True
        self.ai_button.state(["disabled"])
        self._set_text(self.ai_help_text, "KI-Hilfe wird geladen...")
        threading.Thread(target=self._fetch_ai_help_thread, args=(self.active_requirement, api_key), daemon=True).start()

    def _fetch_ai_help_thread(self, requirement, api_key: str) -> None:
        try:
            content = fetch_ai_help(requirement, api_key)
        except Exception as error:
            self.after(0, lambda: self._handle_ai_error(str(error)))
        else:
            self.ai_help_store.save_help(requirement.code, content)
            self.after(0, lambda: self._on_ai_help_ready(requirement.code, content))
        finally:
            self.after(0, self._reset_ai_fetch_state)

    def _handle_ai_error(self, message: str) -> None:
        messagebox.showerror("KI Hilfe", message)

    def _on_ai_help_ready(self, req_code: str, content: str) -> None:
        if self.active_requirement and self.active_requirement.code == req_code:
            self._update_ai_text(content)
            messagebox.showinfo("KI Hilfe", "Neue KI-Hilfe gespeichert.")

    def _reset_ai_fetch_state(self) -> None:
        self._is_fetching_help = False
        if self.active_requirement:
            self.ai_button.state(["!disabled"])
        else:
            self.ai_button.state(["disabled"])

    def _clear_details(self) -> None:
        self.detail_title.config(text="Details")
        self.status_var.set("open")
        self.note_text.delete("1.0", tk.END)
        self.active_requirement = None
        for widget in [self.description_text, self.ai_help_text]:
            self._set_text(widget, "")
        self.ai_button.state(["disabled"])

def parse_args():
    parser = argparse.ArgumentParser(description="GUI fuer das IT-Grundschutz-Kompendium.")
    parser.add_argument("--xml", default="XML_Kompendium_2023.xml", help="Pfad zur XML-Datei.")
    parser.add_argument("--status-file", default="status.json", help="Pfad zur Status-Datei.")
    parser.add_argument("--api-key-file", default="openai_key.txt", help="Pfad zur Datei mit OpenAI-API-Key.")
    parser.add_argument("--ai-help-file", default="ai_help_store.json", help="Pfad zur Datei fuer KI-Hilfen.")
    return parser.parse_args()


def main():
    args = parse_args()
    compendium = load_compendium(Path(args.xml))
    store = StatusStore(Path(args.status_file))
    api_key_store = ApiKeyStore(Path(args.api_key_file))
    ai_help_store = AIHelpStore(Path(args.ai_help_file))
    app = CompendiumApp(compendium, store, api_key_store, ai_help_store)
    app.mainloop()


if __name__ == "__main__":
    main()

