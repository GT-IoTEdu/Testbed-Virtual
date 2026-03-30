-- Migration: Separar zeek_alerts (alertas SSE) de incidents (workflow).
-- 1) A tabela atual zeek_alerts tem estrutura de Incident (device_ip, incident_type, ...).
-- 2) Renomear zeek_alerts -> incidents (para o modelo Incident).
-- 3) Criar nova tabela zeek_alerts com estrutura igual a suricata_alerts/snort_alerts.

RENAME TABLE zeek_alerts TO incidents;

CREATE TABLE zeek_alerts (
  id int(11) NOT NULL AUTO_INCREMENT,
  institution_id int(11) NOT NULL,
  detected_at datetime NOT NULL,
  signature varchar(500) NOT NULL,
  signature_id varchar(50) DEFAULT NULL,
  severity enum('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'MEDIUM',
  src_ip varchar(45) DEFAULT NULL,
  dest_ip varchar(45) DEFAULT NULL,
  src_port varchar(20) DEFAULT NULL,
  dest_port varchar(20) DEFAULT NULL,
  protocol varchar(20) DEFAULT NULL,
  category varchar(255) DEFAULT NULL,
  raw_log_data text DEFAULT NULL,
  processed_at datetime DEFAULT NULL,
  created_at datetime DEFAULT NULL,
  updated_at datetime DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_zeek_alerts_institution_id (institution_id),
  KEY idx_zeek_alerts_detected_at (detected_at),
  KEY idx_zeek_alerts_severity (severity),
  KEY idx_zeek_alerts_src_ip (src_ip),
  KEY idx_zeek_alerts_dest_ip (dest_ip),
  KEY idx_zeek_alerts_processed_at (processed_at),
  CONSTRAINT zeek_alerts_ibfk_1 FOREIGN KEY (institution_id) REFERENCES institutions (id)
);
