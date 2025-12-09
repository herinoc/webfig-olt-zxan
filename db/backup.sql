/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.2-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: nms_db
-- ------------------------------------------------------
-- Server version	11.8.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `config_onu_history`
--

DROP TABLE IF EXISTS `config_onu_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `config_onu_history` (
  `kode_psb` varchar(30) NOT NULL,
  `id_olt` int(11) NOT NULL,
  `jenis_olt` varchar(50) DEFAULT NULL,
  `port_base` varchar(50) DEFAULT NULL,
  `onu_num` varchar(10) DEFAULT NULL,
  `jenis_modem` varchar(100) DEFAULT NULL,
  `sn` varchar(100) DEFAULT NULL,
  `nama_pelanggan` varchar(150) DEFAULT NULL,
  `alamat` text DEFAULT NULL,
  `upload_profile` varchar(50) DEFAULT NULL,
  `download_profile` varchar(50) DEFAULT NULL,
  `vlan` varchar(20) DEFAULT NULL,
  `pppoe_username` varchar(100) DEFAULT NULL,
  `pppoe_password` varchar(100) DEFAULT NULL,
  `lan_lock` enum('lock','open') DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`kode_psb`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `config_onu_history`
--

LOCK TABLES `config_onu_history` WRITE;
/*!40000 ALTER TABLE `config_onu_history` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `config_onu_history` VALUES
('PSB-20250922-0001',1,'C300','1/1/1','1','HG8245','SN1001','Andi Saputra','Jl. Merdeka No.1','UP100','DOWN100','10','andi100','pass100','lock','active','2025-09-22 12:18:49'),
('PSB-20250922-0002',1,'C300','1/1/1','2','ZXHN F660','SN1002','Budi Santoso','Jl. Mawar No.2','UP200','DOWN200','20','budi200','pass200','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0003',1,'C320','1/1/2','1','HG8245','SN1003','Citra Lestari','Jl. Kenanga No.3','UP300','DOWN300','30','citra300','pass300','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0004',2,'C600','1/2/1','1','ZXHN F660','SN1004','Dedi Pratama','Jl. Melati No.4','UP400','DOWN400','40','dedi400','pass400','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0005',2,'C300','1/2/1','2','HG8245','SN1005','Eka Putri','Jl. Anggrek No.5','UP500','DOWN500','50','eka500','pass500','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0006',2,'C320','1/2/2','1','ZXHN F660','SN1006','Fajar Hidayat','Jl. Dahlia No.6','UP600','DOWN600','60','fajar600','pass600','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0007',3,'C600','1/3/1','1','HG8245','SN1007','Gita Ramadhani','Jl. Flamboyan No.7','UP700','DOWN700','70','gita700','pass700','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0008',3,'C300','1/3/1','2','ZXHN F660','SN1008','Hadi Wijaya','Jl. Cempaka No.8','UP800','DOWN800','80','hadi800','pass800','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0009',3,'C320','1/3/2','1','HG8245','SN1009','Indah Purnama','Jl. Bougenville No.9','UP900','DOWN900','90','indah900','pass900','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0010',4,'C600','1/4/1','1','ZXHN F660','SN1010','Joko Susanto','Jl. Kemuning No.10','UP1000','DOWN1000','100','joko1000','pass1000','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0011',4,'C300','1/4/1','2','HG8245','SN1011','Kiki Anggraini','Jl. Sakura No.11','UP1100','DOWN1100','110','kiki1100','pass1100','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0012',4,'C320','1/4/2','1','ZXHN F660','SN1012','Lutfi Ramadhan','Jl. Magnolia No.12','UP1200','DOWN1200','120','lutfi1200','pass1200','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0013',5,'C600','1/5/1','1','HG8245','SN1013','Maya Sari','Jl. Teratai No.13','UP1300','DOWN1300','130','maya1300','pass1300','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0014',5,'C300','1/5/1','2','ZXHN F660','SN1014','Nanda Prasetyo','Jl. Kenanga No.14','UP1400','DOWN1400','140','nanda1400','pass1400','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0015',5,'C320','1/5/2','1','HG8245','SN1015','Okti Fitri','Jl. Mawar No.15','UP1500','DOWN1500','150','okti1500','pass1500','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0016',6,'C600','1/6/1','1','ZXHN F660','SN1016','Putra Rahman','Jl. Anggrek No.16','UP1600','DOWN1600','160','putra1600','pass1600','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0017',6,'C300','1/6/1','2','HG8245','SN1017','Qori Ayu','Jl. Dahlia No.17','UP1700','DOWN1700','170','qori1700','pass1700','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0018',6,'C320','1/6/2','1','ZXHN F660','SN1018','Rizki Hidayat','Jl. Flamboyan No.18','UP1800','DOWN1800','180','rizki1800','pass1800','open','active','2025-09-22 12:18:49'),
('PSB-20250922-0019',7,'C600','1/7/1','1','HG8245','SN1019','Sari Dewi','Jl. Cempaka No.19','UP1900','DOWN1900','190','sari1900','pass1900','lock','inactive','2025-09-22 12:18:49'),
('PSB-20250922-0020',7,'C300','1/7/1','2','ZXHN F660','SN1020','Taufik Hidayat','Jl. Bougenville No.20','UP2000','DOWN2000','200','taufik2000','pass2000','open','active','2025-09-22 12:18:49');
/*!40000 ALTER TABLE `config_onu_history` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `table_olt`
--

DROP TABLE IF EXISTS `table_olt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `table_olt` (
  `id_olt` int(11) NOT NULL AUTO_INCREMENT,
  `ip_address` varchar(45) NOT NULL,
  `vlan` varchar(20) DEFAULT NULL,
  `jenis_olt` varchar(50) DEFAULT NULL,
  `alamat_pop` varchar(100) DEFAULT NULL,
  `username_telnet` varchar(50) DEFAULT NULL,
  `password_telnet` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_olt`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `table_olt`
--

LOCK TABLES `table_olt` WRITE;
/*!40000 ALTER TABLE `table_olt` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `table_olt` VALUES
(1,'192.168.12.1','901','C300','Boyolangu','n0c','j46u4r@2025'),
(2,'192.168.12.9','911','C600','Campurdarat','n0c','j46u4r@2025'),
(3,'192.168.12.4','920','C300','Kauman','n0c','j46u4r@2025'),
(4,'192.168.12.8','905','C300','Kediri','n0c','j46u4r@2025'),
(5,'192.168.12.7','902','C300','Kalidawir','n0c','j46u4r@2025'),
(6,'192.168.12.6','911','C300','Durenan','n0c','j46u4r@2025'),
(7,'192.168.12.3','906','C300','Gandurasi','n0c','j46u4r@2025'),
(22,'192.168.12.5','903','C300','BEJI','n0c','j46u4r@2025');
/*!40000 ALTER TABLE `table_olt` ENABLE KEYS */;
UNLOCK TABLES;
commit;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-09-22 23:18:32
