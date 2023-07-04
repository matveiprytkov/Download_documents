import base64
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import requests

URL = 'https://api-gw.kedo-demo.cloud.astral-dev.ru/api/v3/docstorage/Documents'


class Document:
    def __init__(self, document_id, document_name, document_type, document_status, sender):
        self.document_id = document_id
        self.document_name = document_name
        self.document_type = document_type
        self.document_status = document_status
        self.sender = sender


class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("800x500")
        self.window.title("Скачивание документов")
        self.token_label = tk.Label(self.window, text="Токен:")
        self.token_label.pack(pady=5)
        self.token_entry = tk.Entry(self.window, width=100)
        self.token_entry.pack()

        self.download_dir_label = tk.Label(self.window, text="Папка для скачивания:")
        self.download_dir_label.pack(pady=5)
        self.download_dir_var = tk.StringVar()
        self.download_dir_entry = tk.Entry(self.window, textvariable=self.download_dir_var, width=100)
        self.download_dir_entry.pack()

        self.download_button = tk.Button(self.window, text="Получить документы", command=self.validate_and_download)
        self.download_button.pack()

        self.document_table = ttk.Treeview(self.window, columns=(
            "Document ID", "Document Name", "Document Type", "Sender", "Document Status"
        ))
        self.documents = None
        self.document_table.heading("#0", text="")
        self.document_table.heading("Document ID", text="Id документа")
        self.document_table.heading("Document Type", text="Шаблон документа")
        self.document_table.heading("Document Name", text="Название документа")
        self.document_table.heading("Sender", text="Отправитель")
        self.document_table.heading("Document Status", text="Статус")
        self.document_table.column("#0", stretch=tk.NO)
        self.document_table.pack()
        self.download_selected_button = tk.Button(self.window, text="Скачать выбранные документы",
                                                  command=self.download_selected)
        self.download_selected_button.pack()

        self.token = None
        self.download_dir = None

        self.session = requests.Session()

    def get_headers(self):
        return {
            'kedo-gateway-token-type': 'IntegrationApi',
            'Authorization': f'Bearer {self.token}'
        }

    def validate_and_download(self):
        self.token = self.token_entry.get()
        self.download_dir = Path(self.download_dir_var.get())
        if not self.download_dir.exists():
            messagebox.showerror("Ошибка", "Нет такой папки для скачивания")
        elif not self.token:
            messagebox.showerror("Ошибка", "Введите токен")
        else:
            fetch_documents = self.get_all_documents()
            self.documents = [
                Document(
                    document_id=document['Id'],
                    document_name=document['Name'],
                    document_type=document['DocumentType'],
                    document_status=document['Status'],
                    sender=f"{document['Sender']['Employee']['FirstName']} {document['Sender']['Employee']['LastName']}"

                ) for document in fetch_documents
            ]
            self.populate_document_list(self.documents)

    def populate_document_list(self, documents):
        self.document_table.delete(*self.document_table.get_children())
        for ind, document in enumerate(documents):
            if (self.download_dir / f'{document.document_name}_{document.document_id}.pdf').exists():
                document.document_status = 'Downloaded'
            self.document_table.insert(
                "", tk.END, text=str(ind+1),
                values=(document.document_id,
                        document.document_name, document.document_type, document.sender, document.document_status)
            )

    def download_selected(self):
        selected_documents = self.document_table.selection()

        if len(selected_documents) == 0:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один документ для скачивания")
        elif not self.download_dir.exists():
            messagebox.showerror("Ошибка", "Нет такой папки для скачивания")
        else:
            for item in selected_documents:
                document_id = self.document_table.item(item, "values")[0]
                document_name = self.document_table.item(item, "values")[1]
                self.download_document(document_id=document_id, document_name=document_name)

        messagebox.showinfo("Завершено", "Выбранные документы успешно скачаны.")
        self.populate_document_list(self.documents)

    def get_all_documents(self):
        get_all_document_url = f'{URL}/inbox?OrderBy=DateSent&IsDesc=true' #Эта строка представляет GET-запрос на сервер, используя параметры OrderBy и IsDesc
        return self.session.get(get_all_document_url, headers=self.get_headers()).json()

    def download_document(self, document_name, document_id):
        download_document_url = f'{URL}/{document_id}/download'
        response = self.session.get(download_document_url, headers=self.get_headers())
        file = self.download_dir / f'{document_name}_{document_id}.pdf'
        content = response.content
        file.write_bytes(base64.b64decode(content))

    def run(self):
        self.window.mainloop()


app = App()
app.run()
