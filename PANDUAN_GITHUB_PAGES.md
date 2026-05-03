# PANDUAN SWITCH NETLIFY → GITHUB PAGES

Domain: jayaklampra.com (atau domain kamu sendiri)
Repo: https://github.com/Sidiq-dev/jayaklampra
Hostinger: Registrar domain

---

## LANGKAH 1: AKTIFKAN GITHUB PAGES

1. Buka https://github.com/Sidiq-dev/jayaklampra
2. Klik tab **Settings** (atas)
3. Klik menu **Pages** (kiri)
4. Di **Build and deployment**:
   - **Source**: pilih `Deploy from a branch`
   - **Branch**: pilih `main`
   - **Folder**: `/ (root)`
5. Klik **Save**

Tunggu 1-2 menit, status akan menjadi "Deployed"

---

## LANGKAH 2: TAMBAH CUSTOM DOMAIN

Masih di halaman **Settings → Pages**:

1. Klik **Add a custom domain**
2. Masukkan domain kamu: `jayaklampra.com`
3. Klik **Add domain**
4. GitHub akan menampilkan informasi DNS

**CATATAN**: Jangan klik "Verify DNS" dulu! Update DNS dulu di Hostinger.

---

## LANGKAH 3: UPDATE DNS DI HOSTINGER

### 3.1 Login ke Hostinger
1. Buka https://www.hostinger.co.id
2. Login dengan akun kamu

### 3.2 Masuk ke DNS/Zones
1. Cari domain `jayaklampra.com`
2. Klik **Manage** atau **DNS**
3. Klik menu **DNS / Nameserver** atau **DNS Zones**

### 3.3 Hapus Record Lama (Netlify)
Hapus record yang mengarah ke Netlify:
- Cari record dengan target `netlify.com` atau `netlify.app`
- Hapus semua record tersebut

### 3.4 Tambah A Records Baru
Klik **Add New Record** atau **Tambah DNS**, tambahkan 4 record:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 185.199.108.153 | 3600 |
| A | @ | 185.199.109.153 | 3600 |
| A | @ | 185.199.110.153 | 3600 |
| A | @ | 185.199.111.153 | 3600 |

### 3.5 Tambah Record untuk www
Tambah 1 record lagi:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | www | `sidiq-dev.github.io` | 3600 |

**CATAT PENTING:**
- Field "Name" isi `@` untuk root domain
- Field "Name" isi `www` untuk subdomain www
- TTL: 3600 atau biarkan default

### 3.6 Simpan
Klik **Save** atau **Simpan**

---

## LANGKAH 4: VERIFIKASI DNS

Kembali ke GitHub (Settings → Pages):

1. Tunggu 5-10 menit agar DNS propagate
2. Klik tombol **Verify DNS**
3. Kalau berhasil, akan muncul tanda hijau ✓

**CATAT**: DNS propagation bisa memakan waktu sampai 24 jam, tapi biasanya 5-30 menit.

---

## LANGKAH 5: ENCRYPTED SSL (HTTPS)

Setelah DNS terverifikasi:

1. Masih di halaman **Settings → Pages**
2. Bagian **Custom domain**, klik domain kamu
3. Centang **Enforce HTTPS**
4. GitHub akan otomatis setup SSL gratis dari Let's Encrypt
5. Tunggu beberapa menit sampai SSL aktif

---

## LANGKAH 6: TES WEBSITE

Buka browser dan akses:
- `https://jayaklampra.com` → harusnya muncul website kamu
- `https://www.jayaklampra.com` → juga harusnya muncul

---

## TROUBLESHOOTING

### Website tidak muncul setelah 30 menit?
1. Cek DNS propagation: https://dnschecker.org/
   - Masukkan domain: `jayaklampra.com`
   - Lihat apakah A records sudah mengarah ke GitHub IPs

2. Cek GitHub Pages status:
   - Settings → Pages
   - Lihat apakah status "Deployed"

### Masih tidak bisa?
1. Cek apakah repo GitHub sudah benar:
   - Ada file `index.html` di root?
   - Ada folder `posts/` dan `pages/`?

2. Cek DNS dengan command:
   ```
   nslookup jayaklampra.com
   ```
   Harusnya menunjukkan IP GitHub (185.199.xxx.xxx)

---

## SETELAH SELESAI

- Website jalan di GitHub Pages (gratis unlimited)
- Update cukup: `git push` ke GitHub
- Auto-deploy dalam 1-2 menit setiap push
- Dashboard admin tetap jalan sama

---

## UPDATE KEDepannya

Kalau ada perubahan:
1. Edit di dashboard admin
2. Klik "Generate & Push"
3. GitHub otomatis deploy
4. Website terupdate!

---

## CATATAN PENTING

- Jangan hapus repo GitHub
- Jangan ubah DNS selama proses ini
- Simpan data penting sebelum mengubah DNS
- Kalau domain punya subdomain lain (mail.jayaklampra.com), perlu setting terpisah

---

## BUTUH BANTUAN?

Kalau ada masalah di langkah mana saja, kabari saya dan saya bantu cek!
