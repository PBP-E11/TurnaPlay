# TurnaPlay

### E-11 : 
- Jose Ryu Toari - 2406495981
- Karla Ameera Raswanda - 2406414542
- Muhammad Fahri Muharram - 2406404705
- Muhammad Hadziqul Falah Teguh - 2406437432
- Tangguh Ambha Wahyuga - 2406361536

## Deskripsi Website

TurnaPlay adalah sebuah website yang berfungsi sebagai pusat informasi turnamen esport di Indonesia. Platform ini hadir untuk menjawab masalah yang sering dialami para gamers, yaitu sulitnya menemukan informasi lomba karena tersebar di berbagai akun media sosial seperti instagram. Melalui TurnaPlay, semua informasi turnamen dikumpulkan, disaring, dan diverifikasi agar pengguna bisa mendapatkan data yang akurat dan terstruktur dalam satu tempat. 

Tujuan utama TurnaPlay adalah menghemat waktu para gamers sekaligus membantu penyelenggara menjangkau peserta lebih luas. Dengan fitur pencarian dan filter berdasarkan game, tanggal, serta popularitas, pengguna dapat dengan mudah menemukan turnamen yang sesuai dengan minat dan kemampuannya.

## Daftar Modul

All CRUD operations are for logged in only for the relevant user (or admin) unless noted otherwise

### 1. Competition
* **Create**: create kompetisi admin only
* **Read**: read kompetisi info public (tanggal mulai, hadiah, dll).
* **Update**: update kompetisi info admin only
* **Delete**: delete kompetisi admin only
* **Fields**: PK id, tanggal_mulai, hadiah, thumbnail, etc.

### 2. User
* **Create**: create profile (display name, site username, email, password)
* **Read**: read profile public
* **Update**: update profile
* **Delete**: delete profile/account (mark as inactive).
* **Fields**: PK id, site_username UNIQUE if active, email UNIQUE if active, password, display_name, active

### 3. Account
* **Create**: create account (game category, ingame name)
* **Read**: read account public
* **Update**: - (disabled, delete and create a new account for that)
* **Delete**: delete account (account will be marked as inactive)
* **Fields**: PK id, FK user.id, game_category, ingame_name, active
* **Constraint**: (game_category, ingame_name) UNIQUE if active

### 4. Competition Invite
* **Create**: invite user to join competition
* **Read**: read invite details (related competition, team members, captain)
* **Update**: accept or reject invite
* **Delete**: cancel invite
* **Fields**: PK id, FK user.id, FK competition_id, status

### 5. Team-member (tied to competition_registration and user account)
* **Create**: add account to team
* **Read**: read team members public
* **Update**: -
* **Delete**: remove account from team
* **Fields**: PK id, FK account.id, FK competition_registration.id

### 6. Competition Registration/Team Detail
* **Create**: create team on each registration
* **Read**: show registration/team details and credentials
* **Update**: edit team details, ex. invite members
* **Delete**: cancel pendaftaran kompetisi and disband team
* **Fields**: PK id, status (valid or not)

## Sumber Dataset

Sumber dataset TurnaPlay berasal dari akun Instagram atas nama @infotournament. Dari akun tersebut kami mengambil inspirasi app kami. Akun tersebut menyediakan post-post turnamen dari berbagai game dari berbagai platform seperti Mobile Legend, Valorant, PUBG, dan lain sebagainya. Permohonan izin sudah dilakukan dan kami tentunya akan mencantumkan kredit website kita kepada akun tersebut.

## Role atau peran pengguna

Pada app TurnaPlay, akan tersedia beberapa role yang membantu kelancaran aplikasi:

### Organizer
Merupakan orang/pihak yang menyelenggarakan turnamen. Organizer memiliki akses membuat turnamen dengan ketentuan yang diinginkan seperti jumlah anggota, jumlah hadiah, dll.. Pembuatan turnamen oleh organizer nantinya akan masuk ke display list-list turnamen yang dapat dilihat oleh user.

### User
User merupakan role untuk para pengguna yang sedang mendaftarkan diri untuk masuk ke turnamen. Suatu hal yang harus diperhatikan disini adalah untuk turnamen kelompok; pendaftaran pada suatu turnamen dilakukan oleh leader. Leader disini akan mendaftarkan semua anggota tim dan akan men-receive password untuk satu tim guna sebagai verifikasi anggota-anggota tersebut yang mendaftar saat hari-h mengikuti turnamen.

### Admin
Admin tetap memiliki privilege untuk men-view turnamen dan menambahkan turnamen, meskipun sebenarnya tidak berkepentingan. Namun hak spesialnya adalah dapat men-close suatu turnamen.. Fitur tersebut diadakan guna untuk mencegah adanya turnamen yang telah melanggar SOP dari TurnaPlay.

## Link Deployment PWS
https://muhammad-fahri41-turnaplay.pbp.cs.ui.ac.id
