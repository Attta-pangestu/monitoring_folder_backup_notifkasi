# Struktur Database SQL Server - Plantware Scanner System

## Overview
Dokumen ini menjelaskan struktur database yang terhubung ke SQL Server, khususnya database `staging_PTRJ_iFES_Plantware` yang berisi data scanner dari Plantware.

## Database dan Tabel

### 1. Database: staging_PTRJ_iFES_Plantware

#### A. Tabel: Gwscannerdata
- **Deskripsi:** Tabel data GW Scanner
- **Jumlah Kolom:** 20
- **Struktur Kolom:**
  - `ID` (bigint, NOT NULL) - Primary Key
  - `FROMOCCODE` (nvarchar, NULL)
  - `TOOCCODE` (nvarchar, NULL)
  - `SCANNERUSERCODE` (nvarchar, NULL)
  - `WORKERCODE` (nvarchar, NULL)
  - `FIELDNO` (nvarchar, NULL)
  - `JOBCODE` (nvarchar, NULL)
  - `VEHICLENO` (nvarchar, NULL)
  - `TRANSNO` (nvarchar, NULL)
  - `TRANSDATE` (datetime, NULL)
  - `RECORDTAG` (nvarchar, NULL)
  - `TRANSSTATUS` (nvarchar, NULL)
  - `ISCONTRACT` (nvarchar, NULL)
  - `CREATEDBY` (nvarchar, NULL)
  - `DATECREATED` (datetime, NULL)
  - `INTEGRATETIME` (datetime, NULL)
  - `FLAG` (nvarchar, NULL)
  - `SCANOUTDATETIME` (datetime, NULL)
  - `REVIEWSTATUS` (nvarchar, NULL)
  - `ItechUpdateStatus` (nchar, NOT NULL)

#### B. Tabel: Ffbscannerdata
- **Deskripsi:** Tabel data FFB Scanner
- **Jumlah Kolom:** 24
- **Struktur Kolom:**
  - `ID` (bigint, NOT NULL) - Primary Key
  - `FROMOCCODE` (nvarchar, NULL)
  - `TOOCCODE` (nvarchar, NULL)
  - `SCANNERUSERCODE` (nvarchar, NULL)
  - `WORKERCODE` (nvarchar, NULL)
  - `FIELDNO` (nvarchar, NULL)
  - `TASKNO` (nvarchar, NULL)
  - `RIPE` (numeric, NULL)
  - `UNRIPE` (numeric, NULL)
  - `UNDERRIPE` (numeric, NULL)
  - `OVERRIPE` (numeric, NULL)
  - `ROTTEN` (numeric, NULL)
  - `ABNORMAL` (numeric, NULL)
  - `LOOSEFRUIT` (numeric, NULL)
  - `TRANSNO` (nvarchar, NULL)
  - `TRANSDATE` (datetime, NULL)
  - `RECORDTAG` (char, NULL)
  - `TRANSSTATUS` (nvarchar, NULL)
  - `TRANSTYPE` (nvarchar, NULL)
  - `CREATEDBY` (nvarchar, NULL)
  - `DATECREATED` (datetime, NULL)
  - `INTEGRATETIME` (datetime, NULL)
  - `FLAG` (nvarchar, NULL)
  - `ItechUpdateStatus` (nchar, NOT NULL)

#### C. Tabel: Scanner_User
- **Deskripsi:** Tabel informasi pengguna scanner
- **Jumlah Kolom:** 5
- **Struktur Kolom:**
  - `OC_Code` (nvarchar, NOT NULL)
  - `Scanner_No` (nvarchar, NOT NULL)
  - `Scanner_User` (nvarchar, NOT NULL)
  - `Position` (nchar, NOT NULL)
  - `Update_Status` (nvarchar, NOT NULL)

## Relasi Antar Tabel (Potensial)

### Relasi berdasarkan kolom-kolom yang umum:
- **Gwscannerdata** dan **Ffbscannerdata**:
  - Dapat dihubungkan melalui kolom `SCANNERUSERCODE`, `WORKERCODE`, `FROMOCCODE`, `TOOCCODE`, `FIELDNO`, `TRANSDATE`
- **Gwscannerdata/Ffbscannerdata** dan **Scanner_User**:
  - Dapat dihubungkan melalui kolom `SCANNERUSERCODE` (di tabel scanner) dengan `Scanner_No` atau `Scanner_User` (di tabel Scanner_User)

## Smart Connection Possibilities
1. **Worker Activity Tracking:**
   - Gabungkan data dari Gwscannerdata dan Ffbscannerdata berdasarkan WORKERCODE
   - Analisis produktivitas pekerja berdasarkan jumlah transaksi dan tanggal

2. **Location & Time Analysis:**
   - Gunakan FROMOCCODE, TOOCCODE, dan TRANSDATE untuk melacak pergerakan dan aktivitas pekerja

3. **Performance Metrics:**
   - Gunakan kolom-kolom numerik dari Ffbscannerdata (RIPE, UNRIPE, UNDERRIPE, OVERRIPE, ROTTEN, ABNORMAL, LOOSEFRUIT) untuk menghitung kualitas panen

## Tabel-tabel Referensi Penting

### D. Tabel: Field_Profile
- **Deskripsi:** Tabel informasi profil lapangan
- **Jumlah Kolom:** 23
- **Struktur Kolom:**
  - `OC_Code` (nvarchar, NOT NULL)
  - `Field_No` (nvarchar, NOT NULL)
  - `Field_Division` (nchar, NOT NULL)
  - `Hectare` (int, NOT NULL)
  - `Total_Tasks` (int, NOT NULL)
  - `Total_Trees` (int, NOT NULL)
  - `Rate_Per_Tone` (numeric, NOT NULL)
  - `Interval_Days` (nchar, NOT NULL)
  - `Field_Type` (nvarchar, NOT NULL)
  - `Rate_Type` (nvarchar, NOT NULL)
  - `Yield_Bracket` (nvarchar, NOT NULL)
  - `Tall_Palm` (nvarchar, NOT NULL)
  - `Hilly_Area` (numeric, NOT NULL)
  - `Contract_Field` (nchar, NOT NULL)
  - `Update_Status` (nvarchar, NOT NULL)
  - `Block_Code` (nvarchar, NOT NULL)
  - `ItechDateUpdated` (datetime, NULL)

### E. Tabel: Job_Code
- **Deskripsi:** Tabel informasi kode pekerjaan
- **Jumlah Kolom:** 11
- **Struktur Kolom:**
  - `Exp_Type` (nvarchar, NOT NULL)
  - `Item_No` (nvarchar, NOT NULL)
  - `Sub_No` (nvarchar, NOT NULL)
  - `Code_Desc` (nvarchar, NOT NULL)
  - `Status` (nvarchar, NOT NULL)
  - `Code_Type` (nvarchar, NOT NULL)
  - `Code_Control` (nvarchar, NOT NULL)
  - `Update_Status` (nvarchar, NOT NULL)
  - `JobCode` (nvarchar, NOT NULL)
  - `ItechDateUpdated` (datetime, NULL)
  - `Job_Category` (nvarchar, NULL)

### F. Tabel: OC
- **Deskripsi:** Tabel informasi Organizational Code (cabang/unit kerja)
- **Jumlah Kolom:** 14
- **Struktur Kolom:**
  - `Code` (nvarchar, NOT NULL)
  - `Name` (nvarchar, NOT NULL)
  - `Short_Name` (nvarchar, NOT NULL)
  - `Address_1` (nvarchar, NULL)
  - `Address_2` (nvarchar, NULL)
  - `Address_3` (nvarchar, NULL)
  - `Post_Code` (nvarchar, NULL)
  - `City_Town` (nvarchar, NULL)
  - `State` (nvarchar, NULL)
  - `Country` (nvarchar, NULL)
  - `Category` (nvarchar, NULL)
  - `Region` (nvarchar, NULL)
  - `Company_Code` (nvarchar, NULL)
  - `Update_Status` (nvarchar, NOT NULL)
  - `ItechDateUpdated` (datetime, NULL)

### G. Tabel: Vehicle_Code
- **Deskripsi:** Tabel informasi kendaraan
- **Jumlah Kolom:** 9
- **Struktur Kolom:**
  - `OC_Code` (nvarchar, NOT NULL)
  - `Vehicle_No` (nvarchar, NOT NULL)
  - `Registration_No` (nvarchar, NOT NULL)
  - `Model` (nvarchar, NOT NULL)
  - `Default_Driver_Name` (nvarchar, NOT NULL)
  - `Default_Driver_No` (nvarchar, NOT NULL)
  - `Vechicle_Type` (nvarchar, NOT NULL)
  - `Update_Status` (nvarchar, NOT NULL)
  - `Vehicle_No_Ori` (nvarchar, NOT NULL)
  - `ItechDateUpdated` (datetime, NULL)

### H. Tabel: Company
- **Deskripsi:** Tabel informasi perusahaan
- **Jumlah Kolom:** 6
- **Struktur Kolom:**
  - `Code` (nvarchar, NOT NULL)
  - `Name` (nvarchar, NULL)
  - `Short_Name` (nvarchar, NULL)
  - `Location` (nvarchar, NULL)
  - `Update_Status` (nvarchar, NOT NULL)
  - `ItechDateUpdated` (datetime, NULL)

## Relasi Antar Tabel (Lengkap)

### Relasi Utama:
1. **Gwscannerdata/Ffbscannerdata** → **Field_Profile**:
   - `Gwscannerdata.FIELDNO` = `Field_Profile.Field_No`
   - `Gwscannerdata.FROMOCCODE` = `Field_Profile.OC_Code`

2. **Gwscannerdata** → **Job_Code**:
   - `Gwscannerdata.JOBCODE` = `Job_Code.JobCode`

3. **Gwscannerdata/Ffbscannerdata** → **OC**:
   - `Gwscannerdata.FROMOCCODE` = `OC.Code`
   - `Gwscannerdata.TOOCCODE` = `OC.Code`

4. **Gwscannerdata** → **Vehicle_Code**:
   - `Gwscannerdata.VEHICLENO` = `Vehicle_Code.Vehicle_No`
   - `Gwscannerdata.FROMOCCODE` = `Vehicle_Code.OC_Code`

5. **OC** → **Company**:
   - `OC.Company_Code` = `Company.Code`

## Keterangan Tambahan
- Kolom-kolom dengan tipe `datetime` (TRANSDATE, DATECREATED, INTEGRATETIME, SCANOUTDATETIME) sangat penting untuk analisis berbasis waktu
- Kolom FLAG dan TRANSSTATUS mungkin berisi informasi status dan kontrol kualitas
- Kolom ISCONTRACT di Gwscannerdata mungkin menunjukkan apakah aktivitas pekerja adalah kontraktor atau tidak
- Kolom-kolom RIPE, UNRIPE, UNDERRIPE, OVERRIPE, ROTTEN di Ffbscannerdata digunakan untuk menghitung kualitas panen
- Tabel Field_Profile menyediakan konteks geografis dan operasional untuk data scanner
- Tabel OC menyediakan informasi organisasi/lokasi kerja
- Tabel Job_Code memberikan deskripsi jenis pekerjaan yang dilakukan
- Tabel Vehicle_Code menyediakan informasi kendaraan yang digunakan dalam operasi
