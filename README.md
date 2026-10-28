# 🎙️ Teleprompter by tourrr

Aplikasi teleprompter *floating overlay* modern dan ringan berbasis Python & Tkinter untuk Windows. Dirancang khusus untuk mempermudah presentasi, ujian sidang, webinar, maupun rekaman video dengan tampilan *glassmorphic* yang elegan, fitur anti bocor saat *screen-share*, dan mode tembus klik (*click-through*).

---

## ✨ Fitur Unggulan

- **🛡️ Anti-Screen-Share (Invisible to Audience)**: Menggunakan Win32 API `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)`. Kotak teleprompter **hanya terlihat di monitor fisik Anda** dan otomatis **tidak terlihat/tersembunyi** saat Anda membagikan layar (*share screen*) di **Zoom, Google Meet, Microsoft Teams, Discord, maupun OBS Studio**.
- **👻 Ghost & Lock Mode (Click-Through)**: Menggunakan Win32 `WS_EX_TRANSPARENT`. Kursor mouse dapat menembus jendela teleprompter sehingga Anda bisa mengklik slide PPT, browser, atau aplikasi di baliknya tanpa terhalang.
- **📝 Slide Manager & Script Editor Visual (`Ctrl + E`)**: Fitur CRUD lengkap (Create, Read, Update, Delete, Reorder, Duplicate) dengan antarmuka 2-kolom yang intuitif. Naskah yang diketik langsung muncul secara *realtime* di jendela overlay.
- **⏱️ Presentation Timer Terintegrasi**: Klik kanan untuk mulai/jeda timer durasi bicara Anda secara langsung di header prompter, tekan `Ctrl + R` untuk mereset waktu.
- **🖲️ System Tray Windows (`pystray`)**: Tetap berjalan di latar belakang dengan menu klik kanan di tray taskbar untuk memilih slide secara cepat, reload naskah, atau toggle tampilan.
- **📐 Gestur Mouse & Shortcut Cepat**: Bebas geser (*drag*), ubah ukuran (*resize* grip `⇲`), atur ukuran font (*zoom* naskah), dan ganti slide dengan roda scroll atau keyboard.
- **💾 Penyimpanan Persisten JSON**: Semua naskah tersimpan rapi di [`slides_data.json`](file:///D:/REPO%20GITHUB/Presentasi/slides_data.json).

---

## 🚀 Panduan Instalasi & Prasyarat

### 1. Prasyarat Sistem
- **Sistem Operasi**: Windows 10 (versi 2004+) atau Windows 11.
- **Python**: Versi 3.10 ke atas.

### 2. Instalasi Dependensi
Buka terminal / PowerShell di direktori proyek ini, lalu jalankan:

```bash
pip install -r requirements.txt
```

*(Pustaka yang digunakan hanya `pystray` untuk System Tray dan `pillow` untuk manipulasi ikon).*

---

## 🖥️ Cara Menjalankan Aplikasi

Pilih salah satu metode yang paling nyaman bagi Anda:

1. **Dobel Klik Batch File**:
   Jalankan file [`run_teleprompter.bat`](file:///D:/REPO%20GITHUB/Presentasi/run_teleprompter.bat) langsung dari File Explorer (aplikasi berjalan di latar belakang tanpa memunculkan jendela hitam console).
2. **Melalui Desktop / Start Menu Windows**:
   Jalankan script pembuat shortcut sekali:
   ```bash
   python make_shortcut.py
   ```
   Setelah itu, Anda cukup membuka **Teleprompter by tourrr** melalui icon di Desktop atau Start Menu.
3. **Melalui Terminal**:
   ```bash
   pythonw teleprompter_overlay.py
   ```

---

## ⌨️ Daftar Shortcut & Gestur Lengkap

### 🖱️ Kontrol Mouse
| Gestur Mouse | Fungsi |
| :--- | :--- |
| **Klik Kiri (Tahan & Geser)** | Memindahkan (*drag*) posisi jendela teleprompter di layar |
| **Tarik Pojok Kanan Bawah (`⇲`)** | Mengubah ukuran lebar & tinggi jendela prompter |
| **Scroll Roda Tengah (Wheel)** | Berpindah ke Slide Berikutnya (Scroll ke bawah) / Sebelumnya (Scroll ke atas) |
| **Klik Roda Tengah (Middle Click)** | Toggle **Lock & Ghost Mode** (Mode tembus klik / klik tembus pandang) |
| **Shift + Klik Kiri** | Alternatif Lock & Ghost Mode bagi pengguna Touchpad / Trackpad laptop |
| **Klik Kanan** | Mulai / Jeda (*Play / Pause*) Timer durasi presentasi |
| **Dobel Klik Kiri** | Menutup aplikasi secara instan (*hanya saat tidak terkunci*) |

### ⌨️ Shortcut Keyboard
| Tombol Keyboard | Fungsi |
| :--- | :--- |
| `Panah Kanan` / `Panah Bawah` / `Spasi` / `PageDown` | Berpindah ke Slide Berikutnya (Next) |
| `Panah Kiri` / `Panah Atas` / `Backspace` / `PageUp` | Berpindah ke Slide Sebelumnya (Previous) |
| `Ctrl + E` | Membuka Slide Manager & Script Editor (CRUD Naskah) |
| `Ctrl + S` *(dalam Slide Manager)* | Menyimpan perubahan slide secara permanen ke file JSON |
| `Ctrl + R` | Reset Presentation Timer ke `00:00` |
| `Ctrl + Klik Kiri` | Menyembunyikan / Menampilkan bar judul slide di atas teks |
| `Ctrl + Scroll Mouse` | Memperbesar / Memperkecil ukuran teks (*font size zoom*) |
| `Escape` / `Ctrl + Q` | Menutup aplikasi (*Quit*) |

---

## 📂 Struktur File

```text
Presentasi/
├── teleprompter_overlay.py     # Kode utama aplikasi teleprompter & Tkinter overlay
├── slides_data.json            # Data naskah & slide presentasi aktif (format JSON)
├── run_teleprompter.bat        # Launcher instan Windows tanpa jendela console
├── make_shortcut.py            # Pembuat shortcut Desktop & Start Menu otomatis
├── create_shortcuts.ps1        # Script PowerShell pembuat shortcut
├── generate_icon.py            # Generator icon emerald multi-resolusi
├── app_icon.ico                # File icon aplikasi Windows
├── app_icon.png                # Gambar icon aplikasi high-res
├── requirements.txt            # Dependensi paket Python
└── README.md                   # Dokumentasi panduan penggunaan
```

---

## 💡 Tips Penggunaan Saat Presentasi / Sidang

1. **Atur Posisi Dekat Kamera**: Geser kotak teleprompter ke area atas monitor (tepat di bawah webcam). Dengan begitu, kontak mata Anda akan terlihat selalu menatap audiens atau dosen penguji.
2. **Aktifkan Ghost Mode (`Middle Click` atau `Shift + Klik Kiri`)**: Setelah posisi pas, aktifkan mode ghost. Kursor Anda dapat bebas mengklik slide PowerPoint atau aplikasi di latar belakang tanpa mengganggu jalannya teleprompter.
3. **Bebas Share Screen Tanpa Panik**: Fitur anti-capture secara otomatis melindungi layar naskah Anda agar tidak terekam audiens konferensi video.
