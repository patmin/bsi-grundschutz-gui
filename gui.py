from __future__ import annotations

import argparse
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from practice_guidance import generate_practical_hints
from requirements_parser import Compendium, load_compendium
from status_store import StatusStore, VALID_STATUSES


class CompendiumApp(tk.Tk):
    def __init__(self, compendium: Compendium, store: StatusStore):
        super().__init__()
        self.title("IT-Grundschutz Kompendium - StatusÃ¼bersicht")
        self.geometry("1200x800")

        self.compendium = compendium
        self.store = store
        self.current_module = None
        self.current_requirements = []

        self._build_widgets()
        self._populate_modules()

    def _build_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

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
        ttk.Label(hints_frame, text="Praxis-Impulse").grid(row=0, column=0, sticky="w")
        self.hints_text = tk.Text(hints_frame, wrap="word", height=8)
        self.hints_text.grid(row=1, column=0, sticky="nsew")
        hints_frame.rowconfigure(1, weight=1)

        paned_detail.add(desc_frame, weight=2)
        paned_detail.add(hints_frame, weight=1)

        for widget in [self.description_text, self.hints_text]:
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

    def _populate_requirements(self, module) -> None:
        self._refresh_requirements()
        self._clear_details()

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

        # wenn Filter greift und nichts Ã¼brig bleibt -> Details zurÃ¼cksetzen
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
        self.detail_title.config(text=f"{req.code} - {req.title}")
        status_data = self.store.get(req.code) or {}
        status_val = status_data.get("status", "open")
        note_val = status_data.get("note", "")
        self.status_var.set(status_val)

        self.note_text.delete("1.0", tk.END)
        self.note_text.insert(tk.END, note_val)

        desc = req.description or "Keine Beschreibung gefunden."
        hints = generate_practical_hints(req)

        self._set_text(self.description_text, desc)
        self._set_text(self.hints_text, "\n".join(f"- {hint}" for hint in hints))

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, value)
        widget.configure(state="disabled")

    def _save_status(self) -> None:
        selection = self.requirements_list.curselection()
        if not selection:
            messagebox.showinfo("Hinweis", "Bitte wÃ¤hlen Sie eine Anforderung aus.")
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
        messagebox.showinfo("Gespeichert", f"Status fÃ¼r {req.code} gespeichert.")

    def _clear_details(self) -> None:
        self.detail_title.config(text="Details")
        self.status_var.set("open")
        self.note_text.delete("1.0", tk.END)
        for widget in [self.description_text, self.hints_text]:
            self._set_text(widget, "")


def parse_args():
    parser = argparse.ArgumentParser(description="GUI fÃ¼r das IT-Grundschutz-Kompendium.")
    parser.add_argument("--xml", default="XML_Kompendium_2023.xml", help="Pfad zur XML-Datei.")
    parser.add_argument("--status-file", default="status.json", help="Pfad zur Status-Datei.")
    return parser.parse_args()


def main():
    args = parse_args()
    compendium = load_compendium(Path(args.xml))
    store = StatusStore(Path(args.status_file))
    app = CompendiumApp(compendium, store)
    app.mainloop()


if __name__ == "__main__":
    main()

