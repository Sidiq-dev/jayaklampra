# Jaya Klampra - Admin CMS

Dashboard sederhana untuk mengelola postingan website.

## Cara Pakai

### 1. Buka Dashboard
Klik 2x file `run.bat`

Dashboard akan terbuka di browser: http://localhost:5000

### 2. Import dari WordPress (Pertama Kali)
- Klik tombol **"Import WP"**
- Data akan diimport dari file WordPress export
- Posts akan tersimpan di `data/posts.json`

### 3. Kelola Posts
- **Post Baru** - Klik tombol "Post Baru"
- **Edit** - Klik tombol "Edit" pada post
- **Hapus** - Klik tombol "×" merah
- **Preview** - Klik tombol "Preview" untuk melihat tampilan

### 4. Generate Website
Setelah selesai edit:
- Klik tombol **"Generate Website"**
- File HTML akan terupdate di folder utama
- Website statis siap di-push ke GitHub

## Struktur Folder

```
admin/
├── run.bat          → Klik 2x untuk buka dashboard
├── app.py           → Flask application
├── generate.py      → Generate HTML files
├── data/
│   └── posts.json   → Database posts (JSON)
└── templates/
    ├── index.html   → Dashboard
    ├── edit.html    → Form create/edit
    └── preview.html → Preview post
```

## Catatan Penting

- Dashboard jalan LOKAL di komputer Anda
- Data tersimpan di `data/posts.json`
- File website TIDAK berubah sampai klik "Generate Website"
- Setelah generate, jangan lupa **git push** untuk update website

## Troubleshooting

### Port 5000 sudah dipakai?
Edit `app.py` baris terakhir, ganti port:
```python
app.run(debug=True, port=5001)  # ganti ke port lain
```

### Flask belum terinstall?
Jalankan di terminal:
```
pip install flask
```
