import os
import cv2
import zipfile
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image

class VideoToFramesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("De Vídeo para Imagens")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        self.video_path = ""
        self.output_folder = "frames_output"
        self.zip_name = "frames_output.zip"

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Fundo com CTkImage
        img_path = os.path.join(os.path.dirname(__file__), "Imagens", "background.png")
        pil_img = Image.open(img_path).resize((1920, 1080))
        self.bg_image = ctk.CTkImage(light_image=pil_img, size=(1920, 1080))
        self.bg_label = ctk.CTkLabel(master=self.root, image=self.bg_image, text="")
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.configure(bg="#a12518", bd=10)  # ou a cor que quiser, ex: "#FFC0CB" para rosa claro

        # Container
        self.container = ctk.CTkFrame(self.root, fg_color="#a12518", width=760, height=540)
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        # Elementos
        self.criar_elementos()

    def criar_elementos(self):
        self.title_label = ctk.CTkLabel(self.container, text="Convertor de Vídeo para Imagens", text_color="yellow", font=ctk.CTkFont(family="MS Serif", size=27, weight="bold"))
        self.title_label.pack(pady=10)

        # Área de Arrastar Vídeo
        self.drop_label = ctk.CTkLabel(self.container, text="Arraste o Vídeo Aqui ou Escolha a Opção Selecionar Vídeo", width=500, height=170, text_color="white",
                                       fg_color="black", corner_radius=10, justify="center", font=ctk.CTkFont(family="Times New Roman", size=20))
        self.drop_label.pack(pady=10)
        # Registrar Área de Drop (precisa do .drop_target_register)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.on_drop)

        # Botão para Selecionar Vídeo
        self.select_button = ctk.CTkButton(self.container, text="Selecionar Vídeo", command=self.select_video, corner_radius=20, font=ctk.CTkFont(family="Times New Roman", size=20))
        self.select_button.pack(pady=5)

        # Barra de progresso extração
        self.progress1_label = ctk.CTkLabel (self.container, text="Extração de quadros:", text_color="white", font=ctk.CTkFont(family="Times New Roman", size=20))
        self.progress1_label.pack(pady=(20, 0))
        self.progress1 = ctk.CTkProgressBar(self.container, width=600, height=15, progress_color="yellow", fg_color="black")
        self.progress1.set(0)
        self.progress1.pack(pady=5)

        # Botão iniciar extração
        self.start_button = ctk.CTkButton(self.container, text="Começar", command=self.extract_frames_thread, state="disabled", corner_radius=20, font=ctk.CTkFont(family="Times New Roman", size=20))
        self.start_button.pack(pady=10)

        # Barra de progresso compactação
        self.progress2_label = ctk.CTkLabel(self.container, text="Compactação:", text_color="white", font=ctk.CTkFont(family="Times New Roman", size=20))
        self.progress2_label.pack(pady=(20, 0))
        self.progress2 = ctk.CTkProgressBar(self.container, width=600, height=15, progress_color="yellow", fg_color="black")
        self.progress2.set(0)
        self.progress2.pack(pady=5)

        # Botão download ZIP
        self.download_button = ctk.CTkButton(self.container, text="Download ZIP", command=self.download_zip, state="disabled", corner_radius=20, font=ctk.CTkFont(family="Times New Roman", size=20))
        self.download_button.pack(pady=10)

    def on_drop(self, event):
        file_path = event.data.strip().replace("{", "").replace("}", "")
        if os.path.isfile(file_path) and file_path.lower().endswith(('.mp4', '.avi', '.mov')):
            self.video_path = file_path
            self.drop_label.configure(text=os.path.basename(file_path), fg_color="#3b8ed0")
            self.start_button.configure(state="normal")
        else:
            messagebox.showerror("Arquivo inválido", "Tipos válidos: .mp4, .avi, .mov")

    def select_video(self):
        path = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            self.drop_label.configure(text=os.path.basename(path), fg_color="#3b8ed0")
            self.start_button.configure(state="normal")

    def extract_frames_thread(self):
        self.start_button.configure(state="disabled")
        self.progress1.set(0)
        self.progress2.set(0)
        self.download_button.configure(state="disabled")
        threading.Thread(target=self.extract_frames).start()

    def extract_frames(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            messagebox.showerror("Erro", "Não foi possível abrir o vídeo.")
            self.start_button.configure(state="normal")
            return

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            filename = os.path.join(self.output_folder, f"frame_{count:04d}.png")
            cv2.imwrite(filename, frame)
            count += 1
            self.progress1.set(count / total)
            self.root.update_idletasks()

        cap.release()
        self.progress1.set(1)
        self.progress1_label.configure(text="Extração de quadros: Concluída!")

        # Iniciar zip após extração
        threading.Thread(target=self.zip_frames).start()

    def zip_frames(self):
        self.progress2.set(0)
        file_list = []
        for root_dir, _, files in os.walk(self.output_folder):
            for file in files:
                file_list.append(os.path.join(root_dir, file))

        total = len(file_list)
        with zipfile.ZipFile(self.zip_name, 'w') as zipf:
            for i, file_path in enumerate(file_list):
                zipf.write(file_path, arcname=os.path.basename(file_path))
                self.progress2.set(i / total)
                self.root.update_idletasks()

        self.progress2.set(1)
        self.progress2_label.configure(text="Compactação: Concluída!")
        self.download_button.configure(state="normal")

    def download_zip(self):
        dest = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP", "*.zip")])
        if dest:
            try:
                os.replace(self.zip_name, dest)
                messagebox.showinfo("Sucesso", "Arquivo ZIP salvo com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar ZIP: {e}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = VideoToFramesApp(root)
    root.mainloop()






















