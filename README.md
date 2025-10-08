# TurnaPlay

## E-11 : 
- Jose Ryu Toari - 2406495981
- Karla Ameera Raswanda - 2406414542
- Muhammad Fahri Muharram - 2406404705
- Muhammad Hadziqul Falah Teguh - 2406437432
- Tangguh Ambha Wahyuga - 2406361536

## Deskripsi Website

TurnaPlay adalah sebuah website yang berfungsi sebagai pusat informasi turnamen esport di Indonesia. Platform ini hadir untuk menjawab masalah yang sering dialami para gamers, yaitu sulitnya menemukan informasi lomba karena tersebar di berbagai akun media sosial seperti instagram. Melalui TurnaPlay, semua informasi turnamen dikumpulkan, disaring, dan diverifikasi agar pengguna bisa mendapatkan data yang akurat dan terstruktur dalam satu tempat. 

Tujuan utama TurnaPlay adalah menghemat waktu para gamers sekaligus membantu penyelenggara menjangkau peserta lebih luas. Dengan fitur pencarian dan filter berdasarkan game, tanggal, serta popularitas, pengguna dapat dengan mudah menemukan turnamen yang sesuai dengan minat dan kemampuannya.

## Daftar Modul

All CRUD operations are for logged in only for the relevant user (or admin) unless noted otherwise (with underscore). Fields hanyalah deskripsi singkat sebagian data penting dan bagaimana interaksi antar modul.

### 1. Competition
* **Create**: create kompetisi. _admin only_
* **Read**: read kompetisi info public (tanggal mulai, hadiah, dll).
* **Update**: update kompetisi info. _admin only_
* **Delete**: delete kompetisi. _admin only_
* **Fields**: PK id, tanggal\_mulai, hadiah, thumbnail, etc.

### 2. User
* **Create**: create profile (display name, site username, email, password).
* **Read**: read profile. _public access_
* **Update**: update profile.
* **Delete**: delete profile/account (mark as inactive).
* **Fields**: PK id, site\_username UNIQUE if active, email UNIQUE if active, password, display\_name, active.

### 3. Account
* **Create**: create account (game category, ingame name)
* **Read**: read account _public access_
* **Update**: - (disabled, delete and create a new account for that)
* **Delete**: delete account (account will be marked as inactive)
* **Fields**: PK id, FK user.id, game\_category, ingame\_name, active
* **Constraint**: (game\_category, ingame\_name) UNIQUE if active

### 4. Competition Invite
* **Create**: invite user to join competition
* **Read**: read invite details (related competition, team members, captain)
* **Update**: accept or reject invite
* **Delete**: cancel invite
* **Fields**: PK id, FK user.id, FK competition\_id, status

### 5. Team-member (tied to competition_registration and user account)
* **Create**: add account to team
* **Read**: read team members public
* **Update**: -
* **Delete**: remove account from team
* **Fields**: PK id, FK account.id, FK competition\_registration.id

### 6. Competition Registration/Team Detail
* **Create**: create team on each registration
* **Read**: show registration/team details and credentials
* **Update**: edit team details, ex. invite members
* **Delete**: cancel pendaftaran kompetisi and disband team
* **Fields**: PK id, status (valid or not)

## Sumber Dataset

Sumber dataset TurnaPlay berasal dari akun Instagram atas nama @infotournament [link](https://www.instagram.com/infotournament/). Dari akun tersebut kami mengambil inspirasi app kami. Akun tersebut menyediakan post-post turnamen dari berbagai game dari berbagai platform seperti Mobile Legend, Valorant, PUBG, dan lain sebagainya. Permohonan izin sudah dilakukan dan kami tentunya akan mencantumkan kredit website kita kepada akun tersebut.

## Role atau peran pengguna

Pada app TurnaPlay, akan tersedia beberapa role yang membantu kelancaran aplikasi:

### User
User merupakan role untuk para pengguna yang mendaftarkan diri untuk masuk ke turnamen.
Suatu hal yang harus diperhatikan disini adalah untuk turnamen kelompok; pendaftaran pada suatu turnamen dilakukan oleh leader.
Leader di sini akan mendaftarkan meng-invite anggota tim, di mana masing-masing anggota dapat menerima atau menolak invite bergabung ke dalam tim.
Masing-masing anggota mendaftarkan kredensial akun (seperti nomor kontak dan email) serta detail akun ingame (seperti ingame name) khusus game tersebut.
eader dapat pula membatalkan invite ataupun mengganti anggota tim sebelum dimulainya kompetisi.
Setelah semua anggota menerima invite, status tim akan menjadi valid dan tim berhasil didaftarkan.

### Organizer
Merupakan orang/pihak yang menyelenggarakan turnamen.
Organizer memiliki akses membuat turnamen dengan ketentuan yang diinginkan seperti jumlah anggota, jumlah hadiah, dll.
Pembuatan turnamen oleh organizer nantinya akan masuk ke display list-list turnamen yang dapat dilihat oleh user.
**User dengan role organizer dibuat oleh admin.**

### Admin
Admin tetap memiliki privilege untuk melihat turnamen layaknya user biasa meskipun sebenarnya tidak berkepentingan.
Admin juga dapat mengisi dan mengubah detail turnamen jika pihak organizer tidak dapat melakukan secara langsung.
Hak spesial admin adalah dapat menutup suatu turnamen dan menghapus/mem-ban user/akun.
Fitur tersebut diadakan guna untuk mengatasi situasi adanya turnamen atau pengguna melanggar SOP  dari TurnaPlay.
**User dengan role admin dibuat oleh admin.**

## Link Deployment PWS
https://muhammad-fahri41-turnaplay.pbp.cs.ui.ac.id

## Link Figma Initial Design
https://www.figma.com/design/R7C7dbbCmhe6KncDQrMKRT/Web-Info-Tournament--Copy-?node-id=3-744&t=S281cfROHHyTXYQ2-1
